# Claims Notification

This project is a hybrid on-premise and AWS-based document processing system. It facilitates automated document retrieval, classification, and evaluation by orchestrating a combination of local services and cloud-native AWS components.

---

## 🏠 On-Premise Service

The on-premise component is responsible for initiating the processing pipeline. Its key responsibilities include:

1. **Document Retrieval**:  
   Receives a `doc-id` and fetches the corresponding document from the internal archive.

2. **Cloud Transfer**:  
   Uploads the retrieved document to the designated **S3 bucket** in the relevant AWS account.

3. **Service Invocation**:  
   After successful upload, the on-premise system invokes the AWS-based service, providing:
   - `doc-id`
   - `Meldedatum` (Date of Notification)
   - `Sparte` (Business Line), as identified by the Input Management system

This service is **deployed on OpenShift**. You can find the source code and deployment configuration in the following repository: [link-to-the-repo](link-to-the-repo)

---

## ☁️ AWS Service

The AWS component orchestrates a series of processing jobs using **Lambda functions** and **SageMaker endpoints**. The processing pipeline is executed in the following order:

1. **Preprocessing Job** (Lambda Function)  
2. **Parallel Jobs**  
   - **SD-Typ** (SageMaker Endpoint)  
   - **SD-Objekt** (SageMaker Endpoint)  
   - **Damage Report Job** (Lambda Function)  
3. **Verification Job** (Lambda Function)  
4. **Damage Cause Job** (Lambda Function)  
5. **Evaluation Job** (Lambda Function)

All Lambda functions and SageMaker endpoints are **orchestrated using AWS Step Functions**. This enables a reliable, stateful execution flow in which each step:

- Consumes the output of the previous step
- Enriches the state with its own results
- Passes the updated state forward to the next step in the chain

Only the **Evaluation Job**, which is the final step in the process, returns a response to the on-premise service. This response is a **cleaned and formatted JSON** that includes only the relevant information required downstream. Intermediate artifacts—such as the full extracted text from the preprocessing step or summaries from earlier jobs—are **intentionally dropped** at this point to minimize payload size and ensure response clarity.   

### 🔧 Preprocessing Job (Lambda Function)

The **Preprocessing Job** is the first step in the AWS processing pipeline. It prepares the input data for downstream analysis by performing the following tasks:

1. **Input Handling**  
   The job receives a JSON payload from the on-premise service. This payload contains essential metadata, including the `doc-id`, `Meldedatum`, and `Sparte`.

2. **Document Retrieval**  
   Using the provided `doc-id`, the job locates and retrieves the corresponding PDF document stored in an Amazon S3 bucket.

3. **Text Extraction via AWS Textract**  
   The document is submitted to **AWS Textract** using the `StartDocumentAnalysis` operation, which performs asynchronous text extraction. Textract automatically analyzes the content and structure of each page in the PDF.

4. **Document Type Handling**  
   After receiving the extracted text, the system determines whether the document is a **form-based document**:
   - If **form elements** (e.g., key-value pairs) are detected, a **key-value extraction** method is used to preserve structured data.
   - If no such structure is present, standard **text block extraction** is applied to process unstructured content.

5. **Asynchronous Execution Note**  
   The use of `StartDocumentAnalysis` requires handling asynchronous page-level extraction results, which are retrieved through subsequent polling or event-driven callbacks once processing is complete.

6. **Cost Consideration**  
   AWS Textract currently represents the **largest cost block** within the claims notification application.  
   It incurs an estimated cost of **approximately $1,000 USD per month**, primarily driven by the volume and complexity of PDF documents processed.

---

### SageMaker Endpoints for SD-Objekt & SD-Typ

#### Why Use SageMaker Endpoints with Fine-Tuned BERT Models Instead of AWS Bedrock?

As part of our model selection process, we evaluated fine-tuned **BERT models** deployed via **Amazon SageMaker Endpoints** against state-of-the-art **Claude models** available through **AWS Bedrock**, including:
- Claude 3 Haiku  
- Claude 3 Sonnet  
- Claude 3.5 Sonnet  

While the Claude models delivered strong results, they consistently underperformed compared to our BERT-based models for the tasks of **Schaden-Objekt** and **Schaden-Typ-Kennung**. Performance differences ranged between **4% and 8%**, depending on the Claude variant used.

Although the margin is not drastic, the BERT models demonstrated a reliable edge, leading to our decision to retain them as the preferred solution for production use.

This evaluation may be revisited in the future, particularly as newer foundation models become available. The *GenAI* library from *GHO* could play a key role in that effort, offering unified access to models hosted not only on AWS Bedrock but also across other platforms like *Google Cloud* and *Azure*.

> *Note: The training process for the BERT models will be described in a separate chapter.*

#### Cost Considerations

- The two SageMaker endpoints together currently generate approximately **$500 USD per month** in operational costs. This makes them the **second largest cost driver** in the claims notification application, following AWS Textract.
- There is potential for **cost optimization** by exploring a smaller SageMaker instance type. The current instance type in use is: **`<INSERT INSTANCE TYPE>`**.

---


### 📄 Damage Report Job (Lambda Function)

The **Damage Report Job** is responsible for extracting three pieces of information from the document:

- **Claims Date** (`Schaden-Datum`)
- **Summary**
- **Notifier** (`Melder`)

All three elements are predicted **in a single call** using a single model invocation. This design decision was made after testing showed no measurable performance improvement from breaking the task into separate steps (i.e., three separate model calls). For cost and time considerations all three pieces of information are extracted in one shot.

#### 🔁 Summary as an Input for the BERT models

We also evaluated whether using the generated **summary** as an input to the BERT models for `Schaden-Objekt` and `Schaden-Typ-Kennung` would improve classification accuracy. However, our experiments showed no benefit in providing the summary over the full extracted text. This is likely due to the BERT models' input limitation of **512 tokens**, meaning both the summary and the full text are effectively truncated in similar ways.

#### ✅ Structured Output with Pydantic

This job is the **first in the pipeline to use a `pydantic.BaseModel`** for enforcing response schema validation. The model is required to return a well-structured response or raise a validation error—**no hallucinations or ambiguous formats are accepted**.

This validation is particularly critical for the **Claims Date**, which must be returned as a machine-readable value:
- Either a properly formatted date string (`dd.mm.yyyy`)
- Or `null`, if no claims date can be identified in the document

Returning natural language like _"the claim happened on dd.mm.yyyy"_ would be semantically correct, but operationally unusable, as it complicates downstream parsing and validation.

---

### ✅ Verification Job (Lambda Function)

The **Verification Job** ensures consistency between the outputs of the two independent BERT models:

- `Schaden-Objekt` (Claimed Object)
- `Schaden-Typ-Kennung` (Claim Type)

---

#### 🔍 Why Is Verification Needed?

Although both BERT models operate independently, not all prediction combinations are semantically valid. For example:

- `SD-Objekt: AH` and `SD-Typ: LW` is an invalid pairing.

To handle such cases, we have two options:

1. **Reject** the result and return an error (`INVALID DATA`)
2. **Correct** the result by generating a valid alternative

To reduce the number of rejected cases ("nicht angelegt") and improve integration with the downstream PIA system, we chose the correction path.

This is achieved using:

- **Claude (via AWS Bedrock)** for reasoning
- **`pydantic`** for response schema enforcement
- The **`instructor`** library for structured prediction

> Among many alternatives (e.g., LangChain, LlamaIndex, Marvin), `instructor` was chosen due to its lightweight nature and built-in **retry mechanism**, which proved especially effective in this scenario.

In cases where the BERT models are "uncertain (e.g., differentiating between a **VK** and **KH** claim), Claude is used to make a final, valid decision.

---

#### 🔁 Procedure

In our experiments, we found that the best results are achieved by always passing the **summary** and the **initial BERT predictions** to Claude—regardless of whether the combination is valid.

This allows Claude to either:

- **Confirm** a valid BERT prediction
- **Adjust** an invalid combination to a valid one

In other words, **all predictions go through a confirmation/verification step**, enabling additional consistency and improving the overall quality of the output.

---

#### ⚠️ Exceptions

There are specific edge cases—such as **motor claims** or distinctions between **BR** and **GL** claims—where even valid predictions should **not** be verified. In these scenarios, Claude has a tendency to **overwrite correct results**, leading to unnecessary or incorrect adjustments.

These exceptions will be discussed in more detail in a later chapter.

---


### 🛠️ Damage Cause Job (Lambda Function)

The **Damage Cause Job** is responsible for identifying the **concrete cause of damage** (`SD-URS-ART`) based on the previously predicted claim type (`Schaden-Typ`).

---

#### 🧩 Process Overview

1. The job begins by reading the `Schaden-Typ` prediction.
2. Based on this claim type, a **specific `pydantic.BaseModel`** is dynamically selected. Each claim type has its own schema for the damage cause.
3. Using a **generic prompt**, the selected BaseModel is then used to extract the appropriate **damage cause** from the document.
4. The response is validated through `pydantic`, ensuring structured, predictable output.

---

#### 🔬 (Potential) Room for Improvement

While the current approach is consistent and schema-driven, there is **potential for improvement** in prediction accuracy:

- **Error Analysis**: Before optimizing, it’s important to identify how many mistakes are made in the field `SD-URS-ART` and whether these errors are due to the prompt's (in-)effectiveness.
- **Prompt Specialization**: Instead of using a single generic prompt across all claim types, **custom prompts** per `Schaden-Typ` could improve model performance and precision.
- **Prompt Optimization**: Tools like **[DSPy](https://github.com/stanfordnlp/dspy)** can be explored for **automatic prompt tuning**, potentially yielding more accurate and robust extractions.

This job remains a promising candidate for iterative enhancement as the volume of labeled examples and failure cases increases.

---

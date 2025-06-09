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

### Verification Job

#### Why do we need it?
Both BERT models (Schaden-Objekt & Schaden-Typ-Kennung) make their predictions completely independent one from another, but not all the possible combinations are valid. For instance it would not be a valid combination to return SD-Objekt: AH and SD-Typ: LW 
So we have basically two options either we return an error (INVALID DATA) or we try to fix the prediction. In order to increase the number of predictions, which where put into the PIA system and reduce the number of cases which are "nicht angelegt". Therefore again pydantic in combination with the instructor package was used for the structured prediction. In my opinion it is the best package for structured predictions (although there are a lot of alternatives, e.g. LangChain, LlamaIndex, Marvin, etc.) but instructor is the most light weight and it offers a retry option which I did not see in all the other packages. 
- So all in all if a non-valid combination is provided we use Claude + pydantic + instructor in order to return a valid prediction. For instance if the BERT models ("aren't sure" if it is a VK or KH claim Claude eventually has to make a decision)

#### Proceedure

In various experiments we saw that the best result can be achieved if we pass the summary and the BERT predictions to Claude to get a "confirmation / verification" even if it is a valid combination. So basically all the predictions getting confirmed (if we have a non-valid combination from BERT then a valid prediction is made)

#### Exceptions
Motor claims / BR vs GL claims
For some cases we saw that they should not be verified (in case they are valid) because Claude overwrites the predictions and makes a correct prediction incorrect. This will be elaborated later.




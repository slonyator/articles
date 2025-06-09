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

### SageMaker Endpoints for SD-Object & SD-Typ

#### Why Use SageMaker Endpoints with Fine-Tuned BERT Models Instead of AWS Bedrock?

In our evaluation of different model hosting strategies, we compared the performance of fine-tuned **BERT models** deployed via **Amazon SageMaker Endpoints** against state-of-the-art **Claude models** available through **AWS Bedrock** (including Claude 3 Haiku, Claude 3 Sonnet, and Claude 3.5 Sonnet).

While the Claude models offered competitive results, they consistently underperformed compared to the fine-tuned BERT models **Schaden-Objekt** and **Schaden-Typ-Kennung**. In the future such an evaluation may be revisited, especially as new model versions are released. The *GenAI* library from *GHO* might be a useful resource because it provides access not only to models which are hosted on AWS Bedrock, but also to those offered by other cloud providers, such as *Google* and *Azure*.

The performance difference, while not massive, ranged from **4% to 8%**, depending on the specific Claude variant used for comparison. Given the consistent edge of the BERT-based solution, we opted to continue with our custom-trained models hosted on SageMaker.

> *Note: The training process for the BERT models will be discussed in a separate chapter.*

#### Cost Considerations

- Both SageMaker endpoints together currently incur a cost of **approximately $500 USD per month**, making them the **second largest cost block** in the application after AWS Textract.
- Some cost optimization may be possible by selecting a **smaller instance type** for hosting the BERT models. Currently, the instance type in use is: **`<INSERT INSTANCE TYPE>`**.

---


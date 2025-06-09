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

---


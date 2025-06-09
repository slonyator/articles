# Claims Notification

This project is a hybrid on-premise and AWS-based document processing system. It facilitates automated document retrieval, classification, and evaluation by orchestrating a combination of local services and cloud-native AWS components.

---

## 📦 Technical Setup

### 🏠 On-Premise Service

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

### ☁️ AWS Service

The AWS component orchestrates a series of processing jobs using **Lambda functions** and **SageMaker endpoints**. The processing pipeline is executed in the following order:

1. **Preprocessing Job** (Lambda Function)
2. **Parallel Jobs**
   - **SD-Typ** (SageMaker Endpoint)
   - **SD-Objekt** (SageMaker Endpoint)
   - **Damage Report Job** (Lambda Function)
3. **Verification Job** (Lambda Function)
4. **Damage Cause Job** (Lambda Function)
5. **Evaluation Job** (Lambda Function)


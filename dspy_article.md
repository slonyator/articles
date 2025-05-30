# Abstract / Introduction

## Personal Experience and Motivation
Anyone who has worked with large language models (LLMs), whether for personal or professional projects, knows that some prompts perform better than others. For complex tasks, techniques like *Zero-Shot Learning*, *Few-Shot Learning*, and *Chain-of-Thought* prompting come into play. The term "prompt engineering" has become commonplace, yet it often involves trial-and-error—tweaking text, adding examples, and hoping for better results. While this may seem simple, it quickly becomes tedious and inefficient.

My own frustration with this hit-or-miss approach stemmed from its lack of structure. Switching LLMs or task contexts meant starting from scratch, making prompt engineering repetitive and time-consuming. This led me to discover DSPy—a Python-based toolkit I came across following the DASH Meetup—which provides a systematic approach to optimizing prompts and model performance.

## What is DSPy?
DSPy is a framework designed to streamline the optimization of prompts and model weights for LLMs. It provides an intuitive interface to automate the exploration and refinement of prompts, reducing manual effort while boosting performance. DSPy supports two key optimization strategies:
- **Prompt Optimization**: Automatically refining few-shot examples or instructions to enhance prompt effectiveness.
- **Model Weight Finetuning**: Generating synthetic datasets from program outputs to fine-tune LLM weights.

By leveraging optimization algorithms, DSPy enables developers to achieve consistent, high-quality results efficiently.

## Out-of-Scope
This blog post focuses on DSPy’s core prompt optimization capabilities. The following topics are not covered:
- **Asynchronous Operations**: DSPy supports asynchronous execution with utilities like `dspy.asyncify` for high-throughput environments, but this is beyond our scope.
- **Streaming Capabilities**: Features like streaming outputs with `dspy.streamify` (available in DSPy 2.6.0+) are not discussed.
- **Deployment Strategies**: Deploying DSPy applications with frameworks like FastAPI or MLflow involves specific configurations. Refer to the [official DSPy deployment tutorial](https://dspy.ai/tutorials/deployment/) for details.

# Disclaimer

## Feature Variability Across Versions
DSPy has undergone breaking changes across versions 2.4, 2.5, and 2.6, which may increase maintenance efforts. Developers should review release notes when upgrading to ensure compatibility.

## Limitations (When to Use / Not to Use)
DSPy excels in scenarios requiring systematic prompt optimization but has limitations:
- **Ideal Use Cases**: Best for tasks where manual prompt tweaking is impractical.
- **Less Suitable For**:
  - Simple, one-off tasks where manual prompting suffices.
  - Applications needing extensive asynchronous or streaming features, or specific deployment strategies, where DSPy’s current capabilities may be limited.
  - Integration with frameworks like LangChain, which remains challenging ([DSPy issue #7139](https://github.com/stanfordnlp/dspy/issues/7139), [DSPy issue #1780](https://github.com/stanfordnlp/dspy/issues/1780)).

# DSPy Optimizers

## Overview
DSPy’s optimizers are powerful tools for enhancing AI program performance by automating two key tasks:
1. **Prompt Optimization**: Refining instructions and examples fed to LLMs.
2. **Model Weight Finetuning**: Adjusting the weights of smaller LLMs for better task alignment.

These optimizers, previously called teleprompters, systematically improve LLM-based programs based on metrics like accuracy or cost, as detailed in the [DSPy Optimizers documentation](https://dspy.ai/learn/optimization/optimizers/#__tabbed_1_2).

---

## Prompt Optimization
Prompt optimization focuses on refining the instructions and examples provided to an LLM. DSPy automates this process, generating and improving few-shot examples or natural-language instructions.

### Methodology
The process typically involves:
- **Bootstrapping**: Executing the program on a training set to collect input/output traces.
- **Grounded Proposal Generation**: Proposing optimized instructions or examples based on program logic and outputs.
- **Search**: Using Bayesian or random search to evaluate configurations against a metric (e.g., accuracy).

This approach is ideal for:
- Few-shot classification
- Question answering
- Structured reasoning tasks

Relevant optimizers include:
- `LabeledFewShot`
- `BootstrapFewShot`
- `BootstrapFewShotWithRandomSearch`
- `COPRO`
- `MIPROv2`

---

## Model Weight Finetuning
Some optimizers go beyond prompts to fine-tune the weights of small or tunable LLMs, improving their internal behavior.

### Methodology
This involves:
- **Trace Collection**: Gathering high-quality input/output pairs from program runs.
- **Data Distillation**: Converting traces into synthetic datasets for finetuning.
- **Finetuning**: Applying parameter-efficient updates to align the model with task requirements.

This is best suited for:
- Small LLMs that support finetuning
- Scenarios where model improvement, not just prompting, is needed

The primary optimizer for this is:
- `BootstrapFinetune`

---

## Summary: Two Paths to Optimization
DSPy offers two complementary strategies:
- Optimize **prompts** to improve what you communicate to the model.
- Optimize **model weights** to enhance how the model processes tasks.

These can be combined—for example, using `MIPROv2` for prompt optimization followed by `BootstrapFinetune` for model tuning—to achieve optimal performance.

---

## Detailed Breakdown of Optimizers

| **Optimizer**                        | **Focus**                          | **Description**                                                                 | **Key Parameters**                                                                 | **Use Case**                                                                 |
|--------------------------------------|------------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| `LabeledFewShot`                     | Few-Shot Learning                 | Uses labeled data to construct `k` few-shot examples.                           | `k`, `trainset`                                                                   | Classification tasks with labeled data.                                      |
| `BootstrapFewShot`                   | Automatic Few-Shot Learning        | Generates demonstrations from program runs, validated by a metric.              | `max_bootstrapped_demos`, `max_rounds`                                            | Question answering with limited data.                                       |
| `BootstrapFewShotWithRandomSearch`   | Automatic Few-Shot Learning        | Extends `BootstrapFewShot` with random search for multiple candidates.          | `num_candidate_programs`, `max_bootstrapped_demos`                                | Optimizing RAG pipelines with larger datasets.                              |
| `BootstrapFinetune`                  | Automatic Finetuning               | Distills program outputs into weight updates for finetuning.                    | `num_threads`                                                                     | Improving small LMs for classification tasks.                               |
| `Ensemble`                           | Program Transformations            | Combines multiple programs, sampling a subset for inference.                    | N/A                                                                               | Balancing accuracy and speed in sentiment analysis.                         |
| `COPRO`                              | Instruction Optimization           | Iteratively refines instructions using coordinate ascent over `depth` rounds.   | `depth`, `breadth`                                                                | Complex reasoning tasks requiring refined instructions.                     |
| `MIPROv2`                            | Combined Optimization              | Optimizes examples and instructions using Bayesian Optimization.                | `view_data_batch_size`, `num_candidates`                                          | High-precision tasks like RAG with large LMs and datasets.                  |

This table is informed by sources like [Understanding Optimizers in DSPy](https://medium.com/the-modern-scientist/understanding-optimizers-in-dspy-1ea9451c128b) and [DSPy Optimizers - Weaviate Blog](https://weaviate.io/blog/dspy-optimizers).

---

## Conclusion

DSPy's optimizers have proven to be a transformative tool for automating prompt and model weight optimization, offering a systematic alternative to manual prompt engineering. In our proof-of-concept (PoC), we utilized DSPy to enhance our application's performance on a real dataset, achieving a significant **12% improvement in accuracy score**. To explore model weight finetuning, we employed a synthetic dataset due to limitations with AWS Bedrock, which currently supports weight optimization only in two U.S. regions, not in the Frankfurt region. By using OpenAI models hosted in the U.S. and adhering to data protection requirements with a synthetic dataset, we achieved an impressive **30% accuracy score improvement**. These results demonstrate DSPy's capability to deliver substantial performance gains across both real and synthetic datasets, making it an invaluable tool for developing robust AI systems while addressing regional and technical constraints. Detailed examples showcasing these optimizations are provided in the accompanying Jupyter Notebook.
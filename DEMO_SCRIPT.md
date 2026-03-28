# 🎤 Omni-Bridge: Hackathon Judging Demo Script (4 Minutes)

## 0:00 - 0:30 | The Hook: The Chaos of Reality
*(Screen: Show a collage or quick slide of messy emergency data: a garbled radio transcript, a panicked WhatsApp screenshot, a blurry dashcam photo.)*

**Speaker:**
"Good afternoon, judges. Emergency response systems today are built for structured data—forms, APIs, CAD systems. But crises don't happen in structured data. They happen in panicked voices over static. They happen in blurry dashcam photos. They happen on WhatsApp.

Today, when that messy, multimodal data hits a dispatcher, it creates a bottleneck. Human operators have to listen, read, synthesize, and type it out before a system can act. That latency costs lives.

Enter **Omni-Bridge**. We’ve built a zero-latency, multimodal agentic mesh powered by Vertex AI and Gemini 2.5 Flash, designed to ingest *any* unstructured chaos and deterministically convert it into a structured, verified execution payload."

---

## 0:30 - 1:30 | The Core Technology & Demo 1 (Audio to Action)
*(Screen: Open the Omni-Bridge web application. Point out the 'Sign in with Google' auth and the premium glassmorphic UI. Click on the "GCS Samples" tab.)*

**Speaker:**
"Our architecture is built on a 5-step autonomous agent pipeline. Let’s look at a real-world example: A garbled ER doctor radio call. I'm going to load a raw voice transcript directly from Google Cloud Storage."

*(Action: Click the "Medical ER" sample. The pipeline starts running.)*

**Speaker:**
"Notice the orchestration happening live. 
1. Our **Modality Agent** categorizes the input. 
2. The **Triage Agent** extracts the intent and sets the DEFCON rating.
3. It's routed to our **Medical Specialist Agent**, which extracts patient vitals and symptoms.
4. Then, the most important step: The **Verification Agent**. This is a hard-coded, deterministic rule engine—*not* an LLM. It guarantees anti-hallucination safety by ensuring no critical data is missing before synthesis.
5. Finally, we get our **Action Synthesis**.

*(Action: Point to the AI Insights Panel and JSON Payload)*

"Look at the AI Insights generated: Latency is minimal. The urgency is CRITICAL. We have a clear pipeline summary indicating a STEMI heart attack, and beneath it, a schema-validated JSON execution payload ready to instantly trigger the hospital's EHR and dispatch systems."

---

## 1:30 - 2:30 | Capabilities & Cognitive Skills
*(Screen: Scroll down slightly or showcase the Security & Memory toggles on the UI)*

**Speaker:**
"But enterprise readiness requires more than just extraction. It requires governance. That's why we built a **Dynamic Skill Registry Middleware**.

Notice these toggles down here.
- **Security & Governance:** If a paramedic accidentally transmits a patient's Social Security Number or credit card during the chaos, our PII scrubbing skill intercepts the payload and redacts it natively *before* it logs to the database.
- **Memory Management:** If a massive highway pile-up occurs, we receive hundreds of fragmented calls from different witnesses. Our short-term memory sliding window groups incidents via geolocation radius, preventing our downstream systems from getting DDOS'd by redundant alerts.

All of this telemetry is actively monitored via **Google Analytics** directly integrated into the dashboard."

---

## 2:30 - 3:30 | The Safety Net: Human-In-The-Loop
*(Screen: Bring up the Streamlit app / command center terminal)*

**Speaker:**
"What happens if the Verification Gate fails? What if the audio is so garbled that Gemini isn't completely confident? Omni-Bridge never guesses. It never silently fails. 

If confidence drops below our threshold, the system immediately pushes the payload to a **Google Cloud Pub/Sub** queue. We’ve built a dedicated **Streamlit Command Center** for operators. They can instantly review the raw data side-by-side with the AI’s partial extraction, manually verify the missing fields, and push the payload forward.

We give systems the speed of AI with the safety net of humans."

---

## 3:30 - 4:00 | Scale and Conclusion
*(Screen: Show the Architecture/Kubernetes deployment diagram or terminal showing `kubectl`)*

**Speaker:**
"Omni-Bridge isn't just a prototype; it's a production-ready blueprint. We’ve deployed the stateless FastAPI backend on **Google Cloud Run** for instantaneous auto-scaling, and we have fully defined **Google Kubernetes Engine (GKE)** manifests ready for high-availability enterprise environments.

Omni-Bridge takes the human chaos out of emergency data and replaces it with deterministic machine precision. Thank you, and we're ready for your questions."

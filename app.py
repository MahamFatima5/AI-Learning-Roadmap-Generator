import os
import json
import gradio as gr
from groq import Groq


# ==========================================================
# GROQ CONNECTION
# ==========================================================

api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY is not configured. "
        "Please add it to the environment variables."
    )

client = Groq(api_key=api_key)


# ==========================================================
# SYSTEM PROMPT
# ==========================================================

SYSTEM_PROMPT = """
You are an expert AI learning roadmap designer.

Your job is to create practical, realistic and personalized
learning roadmaps for people who want to learn a specific field.

The user will provide:

1. Domain or field
2. Skill level
3. Learning duration
4. Available study hours per day

Create a roadmap that realistically fits the user's available time.

Divide the roadmap into logical phases.

Each phase must contain:

- phase
- title
- duration
- topics
- practical project

The roadmap must also contain:

- title
- goal
- final capstone project

IMPORTANT:

Return ONLY a JSON object.

Do not return Markdown.

Do not return ```json.

Do not write explanations before or after the JSON.

Use exactly this structure:

{
    "title": "Learning Roadmap",
    "goal": "Description of the learning goal",
    "phases": [
        {
            "phase": "Phase 1",
            "title": "Fundamentals",
            "duration": "2 weeks",
            "topics": [
                "Topic 1",
                "Topic 2",
                "Topic 3"
            ],
            "project": "Practical project description"
        }
    ],
    "final_project": "Final capstone project description"
}

Make the roadmap practical, achievable and appropriate
for the user's skill level and available learning time.
"""


# ==========================================================
# GENERATE ROADMAP
# ==========================================================

def generate_roadmap(domain, level, learning_time, hours_per_day):

    prompt = f"""
Create a personalized learning roadmap.

Domain:
{domain}

Skill Level:
{level}

Learning Duration:
{learning_time}

Available Study Time:
{hours_per_day} hours per day

Create a realistic roadmap that fits these constraints.

The roadmap should contain several learning phases.

Each phase should include:

- phase name
- title
- duration
- important topics
- practical project

Also include a final capstone project.

Return ONLY the JSON object requested by the system instructions.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={
            "type": "json_object"
        },
        temperature=0.5,
        max_completion_tokens=6000
    )

    result = response.choices[0].message.content

    return json.loads(result)


# ==========================================================
# EXTRACT TOPICS
# ==========================================================

def extract_topics(roadmap):

    topics = []

    for phase in roadmap["phases"]:

        for topic in phase["topics"]:

            topics.append(topic)

    return topics


# ==========================================================
# CALCULATE PROGRESS
# ==========================================================

def calculate_progress(completed_topics, all_topics):

    if not all_topics:
        return 0

    completed_count = len(completed_topics)
    total_count = len(all_topics)

    progress = (completed_count / total_count) * 100

    return round(progress)


# ==========================================================
# GENERATE APPLICATION ROADMAP
# ==========================================================

def generate_application_roadmap(
    domain,
    level,
    learning_time,
    hours_per_day
):

    if not domain.strip():

        return (
            "⚠️ Please enter a domain or field.",
            gr.CheckboxGroup(
                choices=[],
                value=[],
                label="Check the topics you have completed",
                interactive=True
            ),
            []
        )

    roadmap = generate_roadmap(
        domain,
        level,
        learning_time,
        hours_per_day
    )

    topics = extract_topics(roadmap)

    # ------------------------------------------------------
    # Build Markdown output
    # ------------------------------------------------------

    markdown = f"# 🎓 {roadmap['title']}\n\n"

    markdown += "## 🎯 Learning Goal\n\n"

    markdown += f"{roadmap['goal']}\n\n"

    # ------------------------------------------------------
    # Add phases
    # ------------------------------------------------------

    for phase in roadmap["phases"]:

        markdown += (
            f"## {phase['phase']}: "
            f"{phase['title']}\n\n"
        )

        markdown += (
            f"**Duration:** "
            f"{phase['duration']}\n\n"
        )

        markdown += "### 📚 Topics\n\n"

        for topic in phase["topics"]:

            markdown += f"- {topic}\n"

        markdown += "\n"

        markdown += "### 💻 Practical Project\n\n"

        markdown += f"{phase['project']}\n\n"

    # ------------------------------------------------------
    # Final project
    # ------------------------------------------------------

    markdown += "## 🏆 Final Capstone Project\n\n"

    markdown += roadmap["final_project"]

    return (
        markdown,

        gr.CheckboxGroup(
            choices=topics,
            value=[],
            label="Check the topics you have completed",
            interactive=True
        ),

        topics
    )


# ==========================================================
# UPDATE PROGRESS
# ==========================================================

def update_progress(completed_topics, all_topics):

    if not all_topics:

        return (
            "### 📊 Progress: 0%",
            0
        )

    progress = calculate_progress(
        completed_topics,
        all_topics
    )

    return (
        f"### 📊 Progress: {progress}%",
        progress
    )


# ==========================================================
# RESET PROGRESS
# ==========================================================

def reset_progress():

    return (
        [],
        "### 📊 Progress: 0%",
        0
    )


# ==========================================================
# GRADIO APPLICATION
# ==========================================================

with gr.Blocks(
    title="AI Learning Roadmap Generator"
) as demo:

    # ------------------------------------------------------
    # HEADER
    # ------------------------------------------------------

    gr.Markdown(
        """
        # 🎓 AI Learning Roadmap Generator

        ### Create a personalized learning roadmap with AI
        """
    )

    # ------------------------------------------------------
    # USER INPUTS
    # ------------------------------------------------------

    gr.Markdown(
        "## 📝 Enter Your Learning Information"
    )

    domain = gr.Textbox(
        label="Domain / Field",
        placeholder="Example: Python Development"
    )

    level = gr.Dropdown(
        choices=[
            "Beginner",
            "Intermediate",
            "Advanced"
        ],
        value="Beginner",
        label="Skill Level"
    )

    learning_time = gr.Textbox(
        label="Learning Duration",
        placeholder="Example: 3 months"
    )

    hours_per_day = gr.Number(
        label="Study Hours Per Day",
        value=2,
        minimum=0.5,
        maximum=12
    )

    # ------------------------------------------------------
    # GENERATE BUTTON
    # ------------------------------------------------------

    generate_btn = gr.Button(
        "🚀 Generate Roadmap",
        variant="primary"
    )

    # ------------------------------------------------------
    # ROADMAP OUTPUT
    # ------------------------------------------------------

    gr.Markdown("---")

    gr.Markdown(
        "## 🗺️ Your Personalized Roadmap"
    )

    roadmap_output = gr.Markdown(
        value="Your roadmap will appear here..."
    )

    # ------------------------------------------------------
    # INTERACTIVE CHECKLIST
    # ------------------------------------------------------

    gr.Markdown("---")

    gr.Markdown(
        "## 📚 Interactive Learning Checklist"
    )

    topic_checklist = gr.CheckboxGroup(
        choices=[],
        value=[],
        label="Check the topics you have completed",
        interactive=True
    )

    # ------------------------------------------------------
    # STATE
    # ------------------------------------------------------

    all_topics_state = gr.State([])

    # ------------------------------------------------------
    # PROGRESS
    # ------------------------------------------------------

    progress_text = gr.Markdown(
        "### 📊 Progress: 0%"
    )

    progress_bar = gr.Slider(
        minimum=0,
        maximum=100,
        value=0,
        step=1,
        label="Learning Progress",
        interactive=False
    )

    # ------------------------------------------------------
    # RESET BUTTON
    # ------------------------------------------------------

    reset_btn = gr.Button(
        "🔄 Reset Progress"
    )

    # ------------------------------------------------------
    # EVENT 1 — GENERATE ROADMAP
    # ------------------------------------------------------

    generate_btn.click(
        fn=generate_application_roadmap,

        inputs=[
            domain,
            level,
            learning_time,
            hours_per_day
        ],

        outputs=[
            roadmap_output,
            topic_checklist,
            all_topics_state
        ]
    )

    # ------------------------------------------------------
    # EVENT 2 — UPDATE PROGRESS
    # ------------------------------------------------------

    topic_checklist.change(
        fn=update_progress,

        inputs=[
            topic_checklist,
            all_topics_state
        ],

        outputs=[
            progress_text,
            progress_bar
        ]
    )

    # ------------------------------------------------------
    # EVENT 3 — RESET PROGRESS
    # ------------------------------------------------------

    reset_btn.click(
        fn=reset_progress,

        inputs=[],

        outputs=[
            topic_checklist,
            progress_text,
            progress_bar
        ]
    )


# ==========================================================
# START APPLICATION
# ==========================================================

if __name__ == "__main__":
    demo.launch()

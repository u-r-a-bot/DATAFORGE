import streamlit as st
import os
import json
import time
from story_assistant import (
    get_api_key, 
    setup_llm_client, 
    generate_chapter, 
    analyze_plot, 
    generate_creative_branches, 
    export_story_context, 
    import_story_context,
    get_audience_guidelines,
    suggest_character_arc,
    generate_plot_outline,
    solve_plot_problem,
    generate_dialogue
)

# Set page configuration
st.set_page_config(
    page_title="Author's AI Assistant",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'story_context' not in st.session_state:
    st.session_state.story_context = {
        "title": "",
        "genre": "",
        "target_age_group": "",
        "characters": [],
        "plot_elements": [],
        "settings": [],
        "timeline_events": []
    }

if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

if 'chapters' not in st.session_state:
    st.session_state.chapters = []

if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []

if 'creative_branches' not in st.session_state:
    st.session_state.creative_branches = []

if 'character_arcs' not in st.session_state:
    st.session_state.character_arcs = []

if 'plot_outlines' not in st.session_state:
    st.session_state.plot_outlines = []

if 'dialogues' not in st.session_state:
    st.session_state.dialogues = []

# UI Components
def sidebar_content():
    st.sidebar.title("Author's AI Assistant")
    
    # API Key input
    api_key = st.sidebar.text_input("Google API Key", type="password", value=st.session_state.api_key)
    if api_key:
        st.session_state.api_key = api_key
    
    st.sidebar.divider()
    
    # Navigation menu
    page = st.sidebar.radio(
        "Navigate",
        ["Story Setup", "Characters", "Settings", "Plot Elements", 
         "Chapter Generator", "Plot Analysis", "Creative Branches",
         "Character Arcs", "Plot Outline", "Dialogue Generator", 
         "Plot Problem Solver", "Export/Import"]
    )
    
    st.sidebar.divider()
    
    # Story status display
    st.sidebar.subheader("Story Status")
    
    if st.session_state.story_context["title"]:
        st.sidebar.write(f"**Title:** {st.session_state.story_context['title']}")
        st.sidebar.write(f"**Genre:** {st.session_state.story_context['genre']}")
        st.sidebar.write(f"**Target Age:** {st.session_state.story_context['target_age_group'].replace('_', ' ').title()}")
        st.sidebar.write(f"**Characters:** {len(st.session_state.story_context['characters'])}")
        st.sidebar.write(f"**Settings:** {len(st.session_state.story_context['settings'])}")
        st.sidebar.write(f"**Plot Elements:** {len(st.session_state.story_context['plot_elements'])}")
        st.sidebar.write(f"**Chapters Created:** {len(st.session_state.chapters)}")
    else:
        st.sidebar.info("Start by setting up your story on the Story Setup page")
    
    return page

def story_setup_page():
    st.header("Story Setup")
    
    # Basic story setup form
    with st.form("story_setup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Story Title", value=st.session_state.story_context["title"])
            
            genre_options = [
                "fantasy", "science_fiction", "mystery", "thriller", 
                "romance", "historical", "literary", "horror", 
                "adventure", "dystopian"
            ]
            genre = st.selectbox(
                "Genre",
                options=genre_options,
                index=genre_options.index(st.session_state.story_context["genre"]) if st.session_state.story_context["genre"] in genre_options else 0
            )
        
        with col2:
            age_group_options = [
                ("children_5_8", "Children (5-8)"),
                ("middle_grade_9_12", "Middle Grade (9-12)"),
                ("young_adult_13_17", "Young Adult (13-17)"),
                ("adult_18+", "Adult (18+)")
            ]
            
            age_group_display = [ag[1] for ag in age_group_options]
            age_group_values = [ag[0] for ag in age_group_options]
            
            selected_index = age_group_values.index(st.session_state.story_context["target_age_group"]) if st.session_state.story_context["target_age_group"] in age_group_values else 2  # Default to YA
            
            age_group_selected = st.selectbox(
                "Target Age Group",
                options=age_group_display,
                index=selected_index
            )
            
            # Map the selected display value back to the actual value
            selected_age_group = age_group_values[age_group_display.index(age_group_selected)]
        
        submit_button = st.form_submit_button("Save Story Settings")
        
        if submit_button:
            st.session_state.story_context["title"] = title
            st.session_state.story_context["genre"] = genre
            st.session_state.story_context["target_age_group"] = selected_age_group
            st.success("Story setup saved successfully!")
    
    # Display audience-specific writing guidelines
    if st.session_state.story_context["target_age_group"]:
        st.subheader("Writing Guidelines for Target Audience")
        age_group = st.session_state.story_context["target_age_group"]
        guidelines = get_audience_guidelines(age_group)
        
        if guidelines:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Vocabulary Level**")
                st.write(guidelines.get("vocabulary_level", "Not specified"))
                
                st.markdown("**Sentence Structure**")
                st.write(guidelines.get("sentence_structure", "Not specified"))
                
                st.markdown("**Thematic Elements**")
                st.write(guidelines.get("thematic_elements", "Not specified"))
            
            with col2:
                st.markdown("**Content Boundaries**")
                st.write(guidelines.get("content_boundaries", "Not specified"))
                
                st.markdown("**Narrative Style**")
                st.write(guidelines.get("narrative_style", "Not specified"))

def characters_page():
    st.header("Character Management")
    
    # Character creation form
    with st.form("character_form"):
        st.subheader("Add a New Character")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Character Name")
            age = st.number_input("Character Age", min_value=0, max_value=1000, value=25)
            
            role_options = ["protagonist", "antagonist", "mentor", "ally", "foil", "love interest", "other"]
            role = st.selectbox("Character's Role", options=role_options)
        
        with col2:
            description = st.text_area("Character Description", placeholder="Physical appearance, personality traits...")
            motivation = st.text_area("Character's Motivation", placeholder="What drives this character?")
        
        submit_button = st.form_submit_button("Add Character")
        
        if submit_button and name:
            # Add character to story context
            character = {
                "name": name,
                "age": age,
                "description": description,
                "role": role,
                "motivation": motivation,
                "traits": [],
                "relationships": []
            }
            
            st.session_state.story_context["characters"].append(character)
            st.success(f"Character '{name}' added successfully!")
    
    # Display existing characters
    if st.session_state.story_context["characters"]:
        st.subheader("Your Characters")
        
        for i, character in enumerate(st.session_state.story_context["characters"]):
            with st.expander(f"{character['name']} ({character['role']})"):
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    st.write(f"**Age:** {character['age']}")
                    st.write(f"**Role:** {character['role']}")
                
                with col2:
                    st.write("**Description:**")
                    st.write(character['description'])
                    
                    st.write("**Motivation:**")
                    st.write(character['motivation'])
                
                with col3:
                    if st.button("Remove", key=f"remove_char_{i}"):
                        st.session_state.story_context["characters"].pop(i)
                        st.experimental_rerun()
    else:
        st.info("No characters added yet. Use the form above to create your first character.")

def settings_page():
    st.header("Setting Management")
    
    # Setting creation form  
    with st.form("setting_form"):
        st.subheader("Add a New Setting")
        
        name = st.text_input("Setting Name", placeholder="e.g., The Enchanted Forest, New York City")
        description = st.text_area("Description", placeholder="Describe the location, atmosphere, time period...")
        significance = st.text_area("Significance to the Plot", placeholder="Why is this setting important?")
        
        submit_button = st.form_submit_button("Add Setting")
        
        if submit_button and name:
            # Add setting to story context
            setting = {
                "name": name,
                "description": description,
                "significance": significance
            }
            
            st.session_state.story_context["settings"].append(setting)
            st.success(f"Setting '{name}' added successfully!")
    
    # Display existing settings
    if st.session_state.story_context["settings"]:
        st.subheader("Your Settings")
        
        for i, setting in enumerate(st.session_state.story_context["settings"]):
            with st.expander(setting['name']):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write("**Description:**")
                    st.write(setting['description'])
                    
                    st.write("**Significance:**")
                    st.write(setting['significance'])
                
                with col2:
                    if st.button("Remove", key=f"remove_setting_{i}"):
                        st.session_state.story_context["settings"].pop(i)
                        st.experimental_rerun()
    else:
        st.info("No settings added yet. Use the form above to create your first setting.")

def plot_elements_page():
    st.header("Plot Elements")
    
    # Plot element creation form
    with st.form("plot_element_form"):
        st.subheader("Add a New Plot Element")
        
        element_type_options = ["conflict", "goal", "twist", "revelation", "obstacle", "backstory", "theme"]
        element_type = st.selectbox("Element Type", options=element_type_options)
        
        description = st.text_area("Description", placeholder="Describe this plot element")
        
        importance_options = ["primary", "secondary", "minor"]
        importance = st.selectbox("Importance", options=importance_options)
        
        submit_button = st.form_submit_button("Add Plot Element")
        
        if submit_button and description:
            # Add plot element to story context
            plot_element = {
                "type": element_type,
                "description": description,
                "importance": importance
            }
            
            st.session_state.story_context["plot_elements"].append(plot_element)
            st.success("Plot element added successfully!")
    
    # Display existing plot elements
    if st.session_state.story_context["plot_elements"]:
        st.subheader("Your Plot Elements")
        
        # Group by importance
        for importance in ["primary", "secondary", "minor"]:
            elements = [elem for elem in st.session_state.story_context["plot_elements"] if elem["importance"] == importance]
            
            if elements:
                st.write(f"**{importance.title()} Elements:**")
                
                for i, element in enumerate(elements):
                    element_index = st.session_state.story_context["plot_elements"].index(element)
                    
                    with st.expander(f"{element['type'].title()}: {element['description'][:50]}..."):
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.write(f"**Type:** {element['type']}")
                            st.write(f"**Description:** {element['description']}")
                        
                        with col2:
                            if st.button("Remove", key=f"remove_plot_{element_index}"):
                                st.session_state.story_context["plot_elements"].pop(element_index)
                                st.experimental_rerun()
    else:
        st.info("No plot elements added yet. Use the form above to create your first plot element.")

def chapter_generator_page():
    st.header("Chapter Generator")
    
    # Check if story is set up
    if not st.session_state.story_context["title"]:
        st.warning("Please set up your story first on the Story Setup page")
        return
    
    # Chapter generation form
    with st.form("chapter_generation_form"):
        st.subheader("Generate a New Chapter")
        
        col1, col2 = st.columns(2)
        
        with col1:
            chapter_title = st.text_input("Chapter Title")
            plot_focus = st.text_area("Plot Focus", placeholder="What should this chapter focus on?")
            tone_options = ["suspenseful", "lighthearted", "somber", "mysterious", "romantic", "action-packed", "reflective"]
            tone = st.selectbox("Tone", options=tone_options)
        
        with col2:
            word_count = st.slider("Approximate Word Count", min_value=500, max_value=5000, value=1500, step=500)
            previous_events = st.text_area("Previously in the Story", placeholder="Briefly describe previous events...")
            current_situation = st.text_area("Current Situation", placeholder="Where does this chapter begin?")
        
        submit_button = st.form_submit_button("Generate Chapter")
        
        if submit_button:
            if not chapter_title or not plot_focus or not current_situation:
                st.error("Please fill in all required fields")
            else:
                with st.spinner("Generating chapter with Gemini... This may take a moment."):
                    # Call the chapter generation function
                    chapter_content = generate_chapter(
                        st.session_state.story_context,
                        chapter_title, 
                        plot_focus, 
                        tone, 
                        word_count, 
                        previous_events, 
                        current_situation
                    )
                    
                    # Add chapter to session state
                    chapter_data = {
                        "title": chapter_title,
                        "content": chapter_content,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.chapters.append(chapter_data)
                    
                    st.success("Chapter generated successfully!")
    
    # Display generated chapters
    if st.session_state.chapters:
        st.subheader("Your Chapters")
        
        for i, chapter in enumerate(st.session_state.chapters):
            with st.expander(f"{chapter['title']} (created: {chapter['timestamp']})"):
                st.markdown(f"## {chapter['title']}")
                st.markdown(chapter['content'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Download Chapter", key=f"download_{i}"):
                        chapter_text = f"# {chapter['title']}\n\n{chapter['content']}"
                        st.download_button(
                            label="Download as Text",
                            data=chapter_text,
                            file_name=f"{chapter['title'].replace(' ', '_')}.md",
                            mime="text/markdown",
                            key=f"download_btn_{i}"
                        )
                
                with col2:
                    if st.button("Delete Chapter", key=f"delete_{i}"):
                        st.session_state.chapters.pop(i)
                        st.experimental_rerun()
    else:
        st.info("No chapters generated yet. Use the form above to create your first chapter.")

def plot_analysis_page():
    st.header("Plot Analysis")
    
    # Check if story is set up
    if not st.session_state.story_context["title"]:
        st.warning("Please set up your story first on the Story Setup page")
        return
    
    # Plot analysis form
    with st.form("plot_analysis_form"):
        st.subheader("Analyze Your Plot")
        
        # Add option to select from existing chapters or paste new content
        analysis_source = st.radio(
            "Select content to analyze",
            ["Use existing chapter", "Paste new text"]
        )
        
        if analysis_source == "Use existing chapter":
            if not st.session_state.chapters:
                st.warning("No chapters available. Generate a chapter first or paste your text.")
                story_excerpt = st.text_area(
                    "Paste Text to Analyze", 
                    placeholder="Or paste the text you want to analyze for plot issues...",
                    height=300
                )
            else:
                # Create a list of chapter titles for selection
                chapter_titles = [chapter["title"] for chapter in st.session_state.chapters]
                selected_chapter = st.selectbox("Select a chapter to analyze", chapter_titles)
                
                # Get the content of the selected chapter
                chapter_index = chapter_titles.index(selected_chapter)
                story_excerpt = st.session_state.chapters[chapter_index]["content"]
                
                # Show a preview
                st.write("Preview (first 200 characters):")
                st.write(story_excerpt[:200] + "..." if len(story_excerpt) > 200 else story_excerpt)
        else:
            story_excerpt = st.text_area(
                "Paste Text to Analyze", 
                placeholder="Paste the text you want to analyze for plot issues...",
                height=300
            )
        
        submit_button = st.form_submit_button("Analyze Plot")
        
        if submit_button:
            if not story_excerpt or len(story_excerpt) < 100:
                st.error("Please provide a substantial story excerpt to analyze (at least 100 characters)")
            else:
                with st.spinner("Analyzing plot with Gemini... This may take a moment."):
                    # Call the plot analysis function
                    analysis_result = analyze_plot(st.session_state.story_context, story_excerpt)
                    
                    # Add analysis to session state
                    analysis_data = {
                        "excerpt_preview": story_excerpt[:100] + "..." if len(story_excerpt) > 100 else story_excerpt,
                        "analysis": analysis_result,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.analysis_results.append(analysis_data)
                    
                    st.success("Analysis complete!")
    
    # Display analysis results
    if st.session_state.analysis_results:
        st.subheader("Analysis Results")
        
        for i, analysis in enumerate(st.session_state.analysis_results):
            with st.expander(f"Analysis {i+1} ({analysis['timestamp']})"):
                st.write("**Excerpt Preview:**")
                st.write(analysis['excerpt_preview'])
                
                st.divider()
                
                st.write("**Analysis:**")
                st.write(analysis['analysis'])
                
                if st.button("Delete Analysis", key=f"delete_analysis_{i}"):
                    st.session_state.analysis_results.pop(i)
                    st.experimental_rerun()
    else:
        st.info("No analyses performed yet. Use the form above to analyze your plot.")
def creative_branches_page():
    st.header("Creative Branching")
    
    # Check if story is set up
    if not st.session_state.story_context["title"]:
        st.warning("Please set up your story first on the Story Setup page")
        return
    
    # Creative branching form
    with st.form("creative_branching_form"):
        st.subheader("Generate Story Branches")
        
        current_situation = st.text_area(
            "Current Situation", 
            placeholder="Describe where your story currently stands..."
        )
        
        decision_point = st.text_area(
            "Key Decision Point", 
            placeholder="What critical decision or event is about to occur?"
        )
        
        num_branches = st.slider("Number of Branches", min_value=2, max_value=5, value=3)
        
        submit_button = st.form_submit_button("Generate Branches")
        
        if submit_button:
            if not current_situation or not decision_point:
                st.error("Please fill in all required fields")
            else:
                with st.spinner("Generating story branches with Gemini... This may take a moment."):
                    # Call the creative branches function
                    branches = generate_creative_branches(
                        st.session_state.story_context,
                        current_situation, 
                        decision_point, 
                        num_branches
                    )
                    
                    # Add branches to session state
                    branch_data = {
                        "decision_point": decision_point,
                        "branches": branches,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.creative_branches.append(branch_data)
                    
                    st.success("Creative branches generated!")
    
    # Display branch results
    if st.session_state.creative_branches:
        st.subheader("Story Branches")
        
        for i, branch_set in enumerate(st.session_state.creative_branches):
            with st.expander(f"Branches for '{branch_set['decision_point'][:50]}...' ({branch_set['timestamp']})"):
                st.write("**Decision Point:**")
                st.write(branch_set['decision_point'])
                
                st.divider()
                
                st.write("**Generated Branches:**")
                st.write(branch_set['branches'])
                
                if st.button("Delete Branches", key=f"delete_branches_{i}"):
                    st.session_state.creative_branches.pop(i)
                    st.experimental_rerun()
    else:
        st.info("No story branches generated yet. Use the form above to explore different plot directions.")

def character_arc_page():
    st.header("Character Arc Generator")
    
    # Check if story is set up and has characters
    if not st.session_state.story_context["title"]:
        st.warning("Please set up your story first on the Story Setup page")
        return
        
    if not st.session_state.story_context["characters"]:
        st.warning("Please add at least one character before generating character arcs")
        return
    
    # Character arc generation form
    with st.form("character_arc_form"):
        st.subheader("Generate Character Arc")
        
        # Get the list of character names
        character_names = [c["name"] for c in st.session_state.story_context["characters"]]
        
        selected_character = st.selectbox(
            "Select Character",
            options=character_names
        )
        
        submit_button = st.form_submit_button("Generate Character Arc")
        
        if submit_button:
            with st.spinner("Generating character arc with Gemini... This may take a moment."):
                # Call the character arc suggestion function
                arc_result = suggest_character_arc(
                    st.session_state.story_context,
                    selected_character
                )
                
                # Add character arc to session state
                arc_data = {
                    "character_name": selected_character,
                    "arc": arc_result,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.character_arcs.append(arc_data)
                
                st.success(f"Character arc for {selected_character} generated successfully!")
    
    # Display character arcs
    if st.session_state.character_arcs:
        st.subheader("Character Arcs")
        
        for i, arc in enumerate(st.session_state.character_arcs):
            with st.expander(f"{arc['character_name']} - Character Arc ({arc['timestamp']})"):
                st.write(arc['arc'])
                
                if st.button("Delete Arc", key=f"delete_arc_{i}"):
                    st.session_state.character_arcs.pop(i)
                    st.experimental_rerun()
    else:
        st.info("No character arcs generated yet. Use the form above to create your first character arc.")

def plot_outline_page():
    st.header("Plot Outline Generator")
    
    # Check if story is set up
    if not st.session_state.story_context["title"]:
        st.warning("Please set up your story first on the Story Setup page")
        return
    
    if not st.session_state.story_context["characters"]:
        st.warning("Please add at least one character before generating a plot outline")
        return
    
    # Plot outline generation form
    with st.form("plot_outline_form"):
        st.subheader("Generate Plot Outline")
        
        num_chapters = st.slider("Number of Chapters", min_value=5, max_value=30, value=10)
        
        submit_button = st.form_submit_button("Generate Plot Outline")
        
        if submit_button:
            with st.spinner("Generating plot outline with Gemini... This may take a moment."):
                # Call the plot outline generation function
                outline_result = generate_plot_outline(
                    st.session_state.story_context,
                    num_chapters
                )
                
                # Add outline to session state
                outline_data = {
                    "num_chapters": num_chapters,
                    "outline": outline_result,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.plot_outlines.append(outline_data)
                
                st.success(f"Plot outline with {num_chapters} chapters generated successfully!")
    
    # Display plot outlines
    if st.session_state.plot_outlines:
        st.subheader("Plot Outlines")
        
        for i, outline in enumerate(st.session_state.plot_outlines):
            with st.expander(f"Plot Outline - {outline['num_chapters']} Chapters ({outline['timestamp']})"):
                st.write(outline['outline'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Download Outline", key=f"download_outline_{i}"):
                        outline_text = outline['outline']
                        st.download_button(
                            label="Download as Text",
                            data=outline_text,
                            file_name=f"plot_outline_{time.strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            key=f"download_outline_btn_{i}"
                        )
                
                with col2:
                    if st.button("Delete Outline", key=f"delete_outline_{i}"):
                        st.session_state.plot_outlines.pop(i)
                        st.experimental_rerun()
    else:
        st.info("No plot outlines generated yet. Use the form above to create your first plot outline.")

def dialogue_generator_page():
    st.header("Dialogue Generator")
    
    # Check if story is set up and has at least two characters
    if not st.session_state.story_context["title"]:
        st.warning("Please set up your story first on the Story Setup page")
        return
        
    if len(st.session_state.story_context["characters"]) < 2:
        st.warning("Please add at least two characters before generating dialogue")
        return
    
    # Dialogue generation form
    with st.form("dialogue_form"):
        st.subheader("Generate Dialogue")
        
        # Get the list of character names
        character_names = [c["name"] for c in st.session_state.story_context["characters"]]
        
        col1, col2 = st.columns(2)
        
        with col1:
            character1 = st.selectbox(
                "Character 1",
                options=character_names,
                key="character1"
            )
        
        with col2:
            character2 = st.selectbox(
                "Character 2",
                options=character_names,
                key="character2",
                index=1 if len(character_names) > 1 else 0
            )
        
        situation = st.text_area(
            "Situation", 
            placeholder="Describe the situation where these characters are interacting..."
        )
        
        tone_options = ["tense", "friendly", "romantic", "confrontational", "comedic", "mysterious", "emotional"]
        tone = st.selectbox("Conversation Tone", options=tone_options)
        
        submit_button = st.form_submit_button("Generate Dialogue")
        
        if submit_button:
            if character1 == character2:
                st.error("Please select two different characters")
            elif not situation:
                st.error("Please describe the situation")
            else:
                with st.spinner("Generating dialogue with Gemini... This may take a moment."):
                    # Call the dialogue generation function
                    dialogue_result = generate_dialogue(
                        st.session_state.story_context,
                        character1, 
                        character2, 
                        situation, 
                        tone
                    )
                    
                    # Add dialogue to session state
                    dialogue_data = {
                        "character1": character1,
                        "character2": character2,
                        "situation": situation,
                        "tone": tone,
                        "dialogue": dialogue_result,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.dialogues.append(dialogue_data)
                    
                    st.success("Dialogue generated successfully!")
    
    # Display dialogues
    if st.session_state.dialogues:
        st.subheader("Generated Dialogues")
        
        for i, dialogue in enumerate(st.session_state.dialogues):
            with st.expander(f"Dialogue: {dialogue['character1']} & {dialogue['character2']} ({dialogue['timestamp']})"):
                st.write(f"**Situation:** {dialogue['situation']}")
                st.write(f"**Tone:** {dialogue['tone']}")
                
                st.divider()
                
                st.write(dialogue['dialogue'])
                
                if st.button("Delete Dialogue", key=f"delete_dialogue_{i}"):
                    st.session_state.dialogues.pop(i)
                    st.experimental_rerun()
    else:
        st.info("No dialogues generated yet. Use the form above to create your first dialogue scene.")

def plot_problem_solver_page():
    st.header("Plot Problem Solver")
    
    # Check if story is set up
    if not st.session_state.story_context["title"]:
        st.warning("Please set up your story first on the Story Setup page")
        return
    
    # Plot problem solving form
    with st.form("plot_problem_form"):
        st.subheader("Solve a Plot Problem")
        
        problem_description = st.text_area(
            "Describe Your Plot Problem", 
            placeholder="What plot challenge are you facing? Be as specific as possible...",
            height=150
        )
        
        submit_button = st.form_submit_button("Get Solutions")
        
        if submit_button:
            if not problem_description:
                st.error("Please describe your plot problem")
            else:
                with st.spinner("Generating solutions with Gemini... This may take a moment."):
                    # Call the plot problem solving function
                    solutions = solve_plot_problem(
                        problem_description,
                        st.session_state.story_context
                    )
                    
                    st.subheader("Solution Suggestions")
                    st.write(solutions)
    
    # Tips for describing plot problems
    with st.expander("Tips for Describing Plot Problems"):
        st.markdown("""
        For the best results, include these details in your problem description:
        
        * **What stage** of the story you're struggling with (beginning, middle, climax, ending)
        * **Which characters** are involved in the problematic section
        * **What you've tried** so far that isn't working
        * **What feeling or effect** you want this part of the story to achieve
        * **Any constraints** you need to work within (e.g., "I can't kill off this character")
        
        Example: "I'm struggling with the middle of my YA fantasy novel. My protagonist (Elara) has discovered her power to communicate with plants, but I can't figure out how to raise the stakes before the final confrontation with the antagonist. I've tried adding a betrayal from her best friend, but it feels clichéd. I want this section to create tension and show Elara's growth, but I can't introduce any new major characters at this point."
        """)

def export_import_page():
    st.header("Export & Import")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Export Story")
        
        if st.session_state.story_context["title"]:
            story_json = export_story_context(st.session_state.story_context)
            
            st.download_button(
                label="Download Story Context as JSON",
                data=story_json,
                file_name=f"{st.session_state.story_context['title'].replace(' ', '_')}_context.json",
                mime="application/json"
            )
        else:
            st.info("Set up your story first to enable export")
    
    with col2:
        st.subheader("Import Story")
        
        uploaded_file = st.file_uploader("Upload a story context JSON file", type=["json"])
        
        if uploaded_file is not None:
            try:
                story_data = json.load(uploaded_file)
                
                if st.button("Import Story Context"):
                    st.session_state.story_context = story_data
                    st.success("Story context imported successfully!")
                    st.experimental_rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON file. Please upload a valid story context file.")

# Main app logic
def main():
    # Display sidebar and get current page
    current_page = sidebar_content()
    
    # Display the appropriate page based on selection
    if current_page == "Story Setup":
        story_setup_page()
    elif current_page == "Characters":
        characters_page()
    elif current_page == "Settings":
        settings_page()
    elif current_page == "Plot Elements":
        plot_elements_page()
    elif current_page == "Chapter Generator":
        chapter_generator_page()
    elif current_page == "Plot Analysis":
        plot_analysis_page()
    elif current_page == "Creative Branches":
        creative_branches_page()
    elif current_page == "Character Arcs":
        character_arc_page()
    elif current_page == "Plot Outline":
        plot_outline_page()
    elif current_page == "Dialogue Generator":
        dialogue_generator_page()
    elif current_page == "Plot Problem Solver":
        plot_problem_solver_page()
    elif current_page == "Export/Import":
        export_import_page()

if __name__ == "__main__":
    main()
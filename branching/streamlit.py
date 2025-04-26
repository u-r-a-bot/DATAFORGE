import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from branching import SimpleVectorDB, preprocess_story, generate_alternatives, create_branch_visualization

# Initialize vector DB in session state
if 'vector_db' not in st.session_state:
    st.session_state.vector_db = SimpleVectorDB()

if 'story_branches' not in st.session_state:
    st.session_state.story_branches = {}

if 'selected_branch_point' not in st.session_state:
    st.session_state.selected_branch_point = None

# api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else os.environ.get("GEMINI_API_KEY")
api_key = "AIzaSyAyBjb3w-583rckUkuvQ9WrZEFxo3NFWhU"
genai.configure(api_key=api_key)

# Initialize Gemini model
gemini_model = genai.GenerativeModel('gemini-1.5-pro')

def main():
    st.title("📝 Writer's Companion: Creative Expansion & Branching")
    st.markdown("Explore alternative story paths and expand your creative possibilities")
    
    with st.sidebar:
        st.header("Story Settings")
        genre = st.selectbox(
            "Select Genre",
            ["Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller", "Historical Fiction"]
        )
        
        st.subheader("Character Information")
        character_info = st.text_area(
            "Provide brief character descriptions",
            "Main character: Sarah - adventurous journalist, 32 years old\n"
            "Supporting character: Marcus - retired detective, skeptical but loyal",
            height=150
        )
    
    story_tab, branch_tab, explore_tab = st.tabs(["Story Input", "Branch Points", "Explore Alternatives"])
    
    with story_tab:
        st.markdown("### Enter your story or outline")
        story_text = st.text_area(
            "Paste your story or detailed outline here",
            "Sarah received a mysterious letter in the mail. It contained coordinates to a location in the mountains and a cryptic message: 'The truth awaits'.\n\n"
            "She debated whether to investigate alone or tell Marcus about it. Marcus had warned her about chasing dangerous leads.\n\n"
            "Sarah decided to call Marcus. He was reluctant but agreed to accompany her.\n\n"
            "They drove to the mountains the next day. The coordinates led to an abandoned research facility.\n\n"
            "At the entrance, they found a keypad requiring a code. Sarah remembered the numbers hidden in the letter.",
            height=300
        )
        
        if st.button("Process Story & Find Branch Points"):
            with st.spinner("Analyzing story structure..."):
                branch_points = preprocess_story(story_text)
                if branch_points == []:
                    st.error("Failed to parse branch points automatically. Please check your story structure.")
                else:
                    st.session_state.branch_points = branch_points
                    st.session_state.story_text = story_text
                    st.success(f"Found {len(branch_points)} potential branch points!")
    
    with branch_tab:
        st.markdown("### Select a Point to Branch Your Story")
        
        if 'branch_points' in st.session_state:
            for i, point in enumerate(st.session_state.branch_points):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Branch Point {i+1}:** {point['description']}")
                with col2:
                    if st.button("Select", key=f"select_{i}"):
                        st.session_state.selected_branch_point = point
                        # Generate alternatives when a branch point is selected
                        with st.spinner("Generating alternative story paths..."):
                            alternatives = generate_alternatives(
                                point, 
                                st.session_state.story_text,
                                character_info,
                                genre
                            )
                            if alternatives == []:
                                st.error("Failed to generate alternatives. Please check your story structure.")
                            else:
                                st.session_state.story_branches[point['id']] = alternatives
                st.divider()
        else:
            st.info("Process your story first to find branch points")
    
    with explore_tab:
        st.markdown("### Explore Alternative Story Paths")
        
        if st.session_state.selected_branch_point and st.session_state.selected_branch_point['id'] in st.session_state.story_branches:
            selected_point = st.session_state.selected_branch_point
            st.markdown(f"#### Branching from: **{selected_point['description']}**")
            
            alternatives = st.session_state.story_branches[selected_point['id']]
            
            # Visualization
            fig = create_branch_visualization(alternatives)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Show alternatives
            for i, alt in enumerate(alternatives):
                with st.expander(f"Path {i+1}: {alt['title']}"):
                    st.markdown(f"**Summary:** {alt['summary']}")
                    st.markdown("**Sample:**")
                    st.markdown(f"*{alt['sample_text']}*")
                    st.markdown(f"**Character Consistency:** {alt['character_consistency']}")
                    
                    if st.button("Expand This Path", key=f"expand_{i}"):
                        with st.spinner("Developing this story branch..."):
                            expand_prompt = f"""
                            Expand this story branch into a full scene or chapter of approximately 400-500 words.
                            
                            ORIGINAL STORY CONTEXT:
                            {st.session_state.story_text}
                            
                            BRANCH POINT:
                            {selected_point['description']}
                            
                            PATH TO EXPAND:
                            {alt['title']} - {alt['summary']}
                            
                            STARTING TEXT:
                            {alt['sample_text']}
                            
                            CHARACTER INFORMATION:
                            {character_info}
                            
                            GENRE:
                            {genre}
                            
                            Write a compelling and coherent continuation. Focus on maintaining the narrative style,
                            character consistency, and advancing the plot in an engaging way.
                            """
                            
                            expanded_response = gemini_model.generate_content(expand_prompt)
                            st.markdown("### Expanded Story Path")
                            st.markdown(expanded_response.text)
        else:
            st.info("Select a branch point first to explore alternatives")

if __name__ == "__main__":
    main()
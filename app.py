import streamlit as st
import pandas as pd
import plotly.express as px
import random

# Set page configuration
st.set_page_config(
    page_title="Automated Timetable Generator",
    page_icon="\U0001F4C5",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
@st.cache_data
def load_data(uploaded_file):
    data = pd.read_csv(uploaded_file)
    data.columns = data.columns.str.strip()  # Remove any leading/trailing spaces in column names
    return data

# Generate timetable with different subjects for each day and class, avoiding back-to-back faculty assignments
def generate_timetable(section, faculty, subjects, rooms):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = ['8:00', '9:00', '10:00', '11:00', '12:00', '1:00', '2:00', '3:00']
    timetable = pd.DataFrame(index=time_slots, columns=days)
    timetable = timetable.fillna("Free")
    
    available_subjects = subjects.sample(frac=1).reset_index(drop=True)  # Shuffle subjects
    subject_index = 0
    faculty_last_assigned = {time: None for time in time_slots}  # Track last faculty for each time slot
    
    for day in days:
        for time in time_slots:
            attempts = 0
            while attempts < len(available_subjects):
                subject_row = available_subjects.iloc[subject_index % len(available_subjects)]
                faculty_member = faculty.loc[faculty['FacultyID'] == subject_row['FacultyID']].iloc[0]
                room = rooms.loc[rooms['RoomID'] == subject_row['RoomID']].iloc[0]
                
                # Ensure no back-to-back faculty assignment
                if faculty_last_assigned[time] != faculty_member['Name']:
                    timetable.loc[time, day] = f"{subject_row['SubjectName']} ({faculty_member['Name']}) - {room['RoomName']}"
                    faculty_last_assigned[time] = faculty_member['Name']
                    subject_index += 1
                    break
                
                subject_index += 1
                attempts += 1
    
    return timetable

# Generate lab report for selected days
def generate_lab_report(timetable, selected_days):
    lab_sessions = timetable[selected_days].applymap(lambda x: x if 'Lab' in x else None)
    lab_report = lab_sessions.stack().reset_index()
    lab_report.columns = ['Time', 'Day', 'Session']
    lab_report = lab_report.dropna()
    return lab_report

# Main app
def main():
    st.title("\U0001F4C5 Automated Timetable Generator")

    st.sidebar.header("\U0001F4E4 Upload Data")
    faculty_file = st.sidebar.file_uploader("Upload Faculty Data (CSV)", type=["csv"])
    subjects_file = st.sidebar.file_uploader("Upload Subjects Data (CSV)", type=["csv"])
    rooms_file = st.sidebar.file_uploader("Upload Rooms Data (CSV)", type=["csv"])

    if faculty_file and subjects_file and rooms_file:
        faculty = load_data(faculty_file)
        subjects = load_data(subjects_file)
        rooms = load_data(rooms_file)

        st.write("### \U0001F468‍🏫 Faculty Data")
        st.dataframe(faculty)
        st.write("### \U0001F4DA Subjects Data")
        st.dataframe(subjects)
        st.write("### \U0001F3EB Rooms Data")
        st.dataframe(rooms)

        sections = ['EEE-A', 'EEE-B', 'EEE-C']
        lab_days = {
            'EEE-A': ['Monday', 'Wednesday'],
            'EEE-B': ['Tuesday', 'Thursday'],
            'EEE-C': ['Friday', 'Monday']
        }

        for section in sections:
            st.write(f"### \U0001F4C6 {section} Timetable (6 Days)")
            timetable = generate_timetable(section, faculty, subjects, rooms)
            st.dataframe(timetable)

            st.write(f"### \U0001F9EA {section} Lab Report ({', '.join(lab_days[section])})")
            lab_report = generate_lab_report(timetable, lab_days[section])
            st.dataframe(lab_report)

            st.write(f"### \U0001F4CA {section} Lab Sessions ({', '.join(lab_days[section])})")
            if not lab_report.empty:
                fig = px.bar(
                    lab_report,
                    x='Time',
                    y='Session',
                    color='Day',
                    barmode='group',
                    title=f"{section} Lab Sessions on {', '.join(lab_days[section])}",
                    labels={'Time': 'Time Slot', 'Session': 'Lab Session'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No lab sessions found for {section} on {', '.join(lab_days[section])}.")

            st.write(f"### \U0001F4E5 Download {section} Lab Report")
            lab_report_csv = lab_report.to_csv(index=False)
            st.download_button(
                label=f"Download {section} Lab Report CSV",
                data=lab_report_csv,
                file_name=f"{section}_lab_report.csv",
                mime='text/csv',
            )

if __name__ == "__main__":
    main()
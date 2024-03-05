import streamlit as st
import mysql.connector
from tabulate import tabulate  # Make sure to install tabulate using: pip install tabulate

# Establish MySQL connection
# Establish MySQL connection
connection = mysql.connector.connect(
    host='database-1.cfs6u6gq4q9q.us-east-1.rds.amazonaws.com', user='admin', password='password', database='mm_team01_01'
)

cursor = connection.cursor()

# Define queries and parameters
queries = {
    "1": {
        "description": "The names of individuals, along with the calories burned, heart rate, for sessions held in filtered Facility Area ",
        "query": "SELECT p.Name, s.Calories_Burned, s.Heart_Rate, f.Area FROM Person p, Session s, WorkoutLocation wl, Facilities f WHERE s.PersonID = p.PersonID AND wl.SessionID = s.SessionID AND f.FacilitiesID = wl.FacilitiesID AND f.Area = %s ORDER BY s.Calories_Burned DESC",
        "parameters": ["Facility_Area_(Ex, Boxing)"]
    },
    "2": {
        "description": "The average heart rate, calories burned, temperature, and humidity for different weather conditions within the specified temperature range.",
        "query": "SELECT w.Weather_Description, ROUND(AVG(s.Heart_Rate),1) AS MeanOfHeartRate, ROUND(AVG(s.Calories_Burned),1) AS MeanOfCaloriesBurned, ROUND(AVG(w.Temperature),1) AS MeanOfTemperature, ROUND(AVG(w.Humidity),1) AS MeanOfHumidity FROM Session s , Weather w WHERE  s.WeatherID = w.WeatherID AND w.Temperature BETWEEN %s AND %s GROUP BY w.Weather_Description",
        "parameters": ["weather_low", "weather_high"]
    },
    "3": {
        "description": "The mean values of heart rate and calories burned during exercise sessions, grouped by the specified age group.",
        "query": "SELECT CASE WHEN TIMESTAMPDIFF(YEAR, p.DOB, CURDATE()) BETWEEN %s AND %s THEN CONCAT('Age: group selected') ELSE 'Other' END AS Age_Group, ROUND(AVG(s.Heart_Rate),1) AS MeanOfHeartRate, ROUND(AVG(s.Calories_Burned),1) AS MeanOfCaloriesBurned FROM Person p, Session s WHERE p.PersonID=s.PersonID GROUP BY Age_Group",
        "parameters": ["Min_Age", "Max_Age"]
    },
    "4": {
        "description": "The program length, completion rate, and average calories burned per session for programs ending on or before the specified end date.",
        "query": "SELECT COUNT(s.ProgramID) AS Program_Length, COUNT(CASE WHEN CURRENT_DATE >= p.Start_Date AND CURRENT_DATE <= p.End_Date THEN 1 END) / COUNT(*) AS Completion_Rate, ROUND(AVG(s.Calories_Burned), 1) AS Avg_CaloriesBurned_PerSession FROM Program p JOIN Session s ON p.ProgramID = s.ProgramID WHERE p.End_Date <= %s;",
        "parameters": ["End_Date_YYYY-MM-DD"] 
    },
    "5": {
        "description": "The average duration and intensity for each specified exercise, grouped by exercise name.",
        "query": "SELECT Excersice_Name, AVG(Duration) AS Avg_Duration, AVG(Intensity) AS Avg_Intensity FROM Exercise WHERE Excersice_Name IN (%s, %s, %s) GROUP BY Excersice_Name ORDER BY Avg_Duration DESC",
        "parameters": ["Exercise_Name_1", "Exercise_Name_2", "Exercise_Name_3"]
    },
    "6": {
        "description": "The total calories burned during exercise sessions for each person, filtered by the specified threshold.",
        "query": "SELECT p.Name, SUM(s.Calories_Burned) as Total_Calories FROM Person p, Session s WHERE p.PersonID = s.PersonID GROUP BY p.Name HAVING SUM(s.Calories_Burned) > %s ORDER BY Total_Calories DESC",
        "parameters": ["Calories_Threshold_(Example 1000)"]
    },
    "7": {
        "description": "The most popular facility areas based on the user-provided workout type, along with the session count for each.",
        "query": "SELECT f.Area, e.Excersice_name,COUNT(wl.SessionID) AS Session_Count FROM Facilities f JOIN WorkoutLocation wl ON f.FacilitiesID = wl.FacilitiesID  JOIN Session s ON s.SessionID = wl.SessionID   JOIN  Exercise e ON e.ExcerciseID = s.ExerciseID  WHERE e.Excersice_name = %s GROUP BY f.Area,e.Excersice_name ORDER BY Session_Count DESC",
        "parameters": ["exercise_name_(Ex. Type 1)"]
    },
    "8": {
        "description": "The stress level and workout performance, including the average heart rate and calories burned, for the specified age group.",
        "query": "SELECT l.StressLevel, ROUND(AVG(s.Heart_Rate),1) AS Avg_Heart_Rate, ROUND(AVG(s.Calories_Burned),1) AS Avg_Calories_Burned FROM LifeStyle l JOIN Session s ON l.PersonID = s.PersonID JOIN Person p ON p.PersonID = l.PersonID WHERE TIMESTAMPDIFF(YEAR, p.DOB, CURDATE())BETWEEN %s AND %s GROUP BY l.StressLevel ORDER BY l.StressLevel",
        "parameters": ["Min_Age", "Max_Age"]
    },
    "9": {
        "description": "The facilities where people burned more calories on average during specific time slots, along with the average calories burned for each facility area.",
        "query": "SELECT f.Area, AVG(s.Calories_Burned) AS Average_CaloriesBurned FROM Facilities f JOIN WorkoutLocation wl ON f.FacilitiesID = wl.FacilitiesID JOIN Session s ON s.SessionID = wl.SessionID  JOIN Program p ON p.ProgramID = s.ProgramID WHERE p.Start_Date BETWEEN %s AND %s GROUP BY f.Area ORDER BY Average_CaloriesBurned DESC",
        "parameters": ["Start_Time_YYYY-MM-DD", "End_Time__YYYY-MM-DD"]
    }
}

import pandas as pd

# Function to execute a selected query
def run_query(query_key, parameter_values=None):
    query_data = queries.get(query_key)

    if query_data:
        query = query_data["query"]
        parameters = query_data.get("parameters", [])

        # Execute the query with parameters if they exist
        if parameters and parameter_values:
            try:
                cursor.execute(query, parameter_values)
            except mysql.connector.Error as err:
                return f"Error executing the query: {err}"

        # Execute the query without parameters
        else:
            try:
                cursor.execute(query)
            except mysql.connector.Error as err:
                return f"Error executing the query: {err}"

        # Fetch and return results as a DataFrame
        results = cursor.fetchall()
        headers = [x[0] for x in cursor.description]
        df = pd.DataFrame(results, columns=headers)
        return df

# Main Streamlit app
def main():
    st.title("Fitness Tracker Database Query App")

    # Display all query descriptions on the left
    st.sidebar.title("Available Queries")
    for key, query_data in queries.items():
        st.sidebar.write(f"{key}: {query_data['description']}")

    # Get user input for the selected query
    query_choice = st.sidebar.text_input("Enter the query number:")

    # Check if the entered value is a valid query number
    if query_choice in queries:
        query_data = queries[query_choice]
        parameters = query_data.get("parameters", [])

        # Display selected query name and description
        st.subheader("Selected Query:")
        st.write(f"Name: {query_choice}")
        st.write(f"Description: {query_data['description']}")

        # Get parameter values if parameters exist
        parameter_values = []
        for param in parameters:
            value = st.text_input(f"Enter value for {param.replace('_', ' ')}:")
            parameter_values.append(value)

        # Execute query on button click
        if st.button("Run Query"):
            results_df = run_query(query_choice, parameter_values)

            # Display results
            if not results_df.empty:
                st.subheader("Query Results:")
                st.write(results_df)

                # Add button to export to CSV
                csv_file = results_df.to_csv(index=False)
                st.download_button(
                    label="Export to CSV",
                    data=csv_file,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
    else:
        st.sidebar.warning("Please enter a valid query number.")

if __name__ == "__main__":
    main()
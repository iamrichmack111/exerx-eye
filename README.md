# ExerxEye

**Exercise Intelligence & Analytics**

ExerxEye is a terminal-first training intelligence platform that combines exercise discovery, workout construction, persistent set history, progress analytics, comparison tools, a REST API, and operational health diagnostics.

## Product surfaces

- `exerx-eye tui` — keyboard-first Textual interface
- `exerx-eye search` — fast exercise discovery
- `exerx-eye random` — randomized exercise selection
- `exerx-eye stats` — dataset/training analytics
- `exerx-eye doctor` — database/system health checks
- FastAPI REST service for programmatic access


Here's the updated `README.md` with detailed information on how to query the API, including all possible queries by headers and the newly added endpoints.

---

# Gym Exercise Search API

This FastAPI application allows users to query a dataset of gym exercises and retrieve exercises based on specific criteria, such as equipment, target muscles, variation, utility, mechanics, and more. It supports retrieving random exercises by muscle groups and lists all available muscle groups.

## Project Setup

1. **Install dependencies**:

   Install the required Python packages by running the following command:

   ```bash
   pip install fastapi pandas hypercorn
   ```

2. **Run the Application**:

   Use Hypercorn to run the FastAPI server:

   ```bash
   hypercorn app:app --reload
   ```

3. **Access the API**:

   The API will be available at `http://127.0.0.1:8000/`.

## Dataset

The dataset used for this application is in CSV format, with the following headers:

### CSV Headers:

- **Exercise Name**: The name of the exercise (e.g., "Bench Press").
- **Equipment**: The equipment required for the exercise (e.g., "Barbell").
- **Variation**: The variation of the exercise (e.g., "Back Squat").
- **Utility**: The utility or purpose of the exercise (e.g., "Strength").
- **Mechanics**: The mechanics type of the exercise (e.g., "Compound").
- **Force**: The direction of force applied during the exercise (e.g., "Push" or "Pull").
- **Preparation**: The setup/preparation steps for the exercise.
- **Execution**: The execution or performance instructions for the exercise.
- **Target_Muscles**: The primary muscles targeted by the exercise (e.g., "Quadriceps", "Hamstrings").
- **Synergist_Muscles**: Secondary muscles that assist the primary muscles.
- **Stabilizer_Muscles**: Muscles responsible for stabilizing the body during the exercise.
- **Antagonist_Muscles**: Muscles that oppose the primary muscles during the exercise.
- **Dynamic_Stabilizer_Muscles**: Muscles responsible for stabilizing joints dynamically during the exercise.
- **Main_muscle**: The main muscle worked in the exercise.
- **Difficulty (1-5)**: The difficulty rating of the exercise, where 1 is easiest and 5 is hardest.
- **Secondary Muscles**: Additional muscles engaged during the exercise.
- **parent_id**: Used for referencing variations of exercises (if applicable).

## Querying the API

Below are the available endpoints, including detailed examples of how to query the API for various exercise-related information.

### 1. **Search for Exercises Based on Column and Value**

You can search for exercises by providing a column (header) and a value to search for. For example, you can search for exercises by equipment, target muscles, variation, and more.

#### Endpoint:
```bash
GET /search?column=<column>&value=<value>
```

#### Example Queries:

- **Search for exercises using a Barbell:**
  ```bash
  http://127.0.0.1:8000/search?column=Equipment&value=Barbell
  ```

- **Search for exercises targeting the Quadriceps:**
  ```bash
  http://127.0.0.1:8000/search?column=Target_Muscles&value=Quadriceps
  ```

### 2. **Get 6 Random Exercises for Each Muscle**

This endpoint allows you to retrieve up to 6 random exercises for each muscle group. You can also specify a muscle group and get only 6 exercises for that muscle.

#### Endpoint:
```bash
GET /six_exercises_per_muscle?muscle=<muscle_name>  # Optional muscle query parameter
```

#### Example Queries:

- **Get 6 random exercises for all muscles:**
  ```bash
  http://127.0.0.1:8000/six_exercises_per_muscle
  ```

- **Get 6 random exercises targeting the Hamstrings:**
  ```bash
  http://127.0.0.1:8000/six_exercises_per_muscle?muscle=Hamstrings
  ```

### 3. **Get One Random Exercise for Each Muscle**

This endpoint allows you to retrieve one random exercise for each muscle group. You can also specify a muscle group and get only one exercise for that muscle.

#### Endpoint:
```bash
GET /one_exercise_per_muscle?muscle=<muscle_name>  # Optional muscle query parameter
```

#### Example Queries:

- **Get one random exercise for all muscles:**
  ```bash
  http://127.0.0.1:8000/one_exercise_per_muscle
  ```

- **Get one random exercise targeting the Quadriceps:**
  ```bash
  http://127.0.0.1:8000/one_exercise_per_muscle?muscle=Quadriceps
  ```

### 4. **List All Available Muscles**

This endpoint lists all the unique muscle groups available in the dataset.

#### Endpoint:
```bash
GET /list_muscles
```

#### Example Query:
```bash
http://127.0.0.1:8000/list_muscles
```

#### Example Output:
```json
{
    "muscles": [
        "Quadriceps",
        "Hamstrings",
        "Pectorals",
        "Triceps",
        "Biceps",
        "Shoulders",
        "Glutes",
        "Calves",
        "Core",
        "Lower Back",
        "Lats",
        "Forearms",
        "Hip Flexors"
    ]
}
```

### 5. **Search by Specific Headers**

Here are additional endpoints for querying by specific headers from the dataset. These endpoints make it easier to search without specifying the `column` parameter explicitly.

#### Endpoint for Searching by Equipment:
```bash
GET /search_by_equipment?equipment=<equipment_name>
```

#### Example Query:
```bash
http://127.0.0.1:8000/search_by_equipment?equipment=Barbell
```

#### Endpoint for Searching by Variation:
```bash
GET /search_by_variation?variation=<variation_name>
```

#### Example Query:
```bash
http://127.0.0.1:8000/search_by_variation?variation=Back%20Squat
```

#### Endpoint for Searching by Utility:
```bash
GET /search_by_utility?utility=<utility_name>
```

#### Example Query:
```bash
http://127.0.0.1:8000/search_by_utility?utility=Strength
```

#### Endpoint for Searching by Mechanics:
```bash
GET /search_by_mechanics?mechanics=<mechanics_name>
```

#### Example Query:
```bash
http://127.0.0.1:8000/search_by_mechanics?mechanics=Compound
```

#### Endpoint for Searching by Force:
```bash
GET /search_by_force?force=<force_name>
```

#### Example Query:
```bash
http://127.0.0.1:8000/search_by_force?force=Push
```

### Error Handling

- If you query an invalid column or muscle name, you will receive an appropriate error message.
- Example error response for invalid column:
  ```json
  {
    "error": "Invalid column name: <column_name>. Available columns: [list of valid columns]"
  }
  ```

## Example Dataset

Here’s a sample row from the dataset:

```csv
Exercise Name,Equipment,Variation,Utility,Mechanics,Force,Preparation,Execution,Target_Muscles,Synergist_Muscles,Stabilizer_Muscles,Antagonist_Muscles,Dynamic_Stabilizer_Muscles,Main_muscle,Difficulty (1-5),Secondary Muscles,parent_id
Squat,Barbell,Back Squat,Strength,Compound,Push,"Stand with feet shoulder-width apart",Lower the barbell to a full squat position,Quadriceps,Hamstrings,Core,Lower Back,Hip Flexors,Quadriceps,4,Hamstrings,2
```

## Additional Information

- **Project Structure**:
  - `app.py`: The main FastAPI application.
  - `gym_exercise_dataset.csv`: The dataset file containing all exercises.
  
- **Dependencies**:
  - `fastapi`: The web framework.
  - `pandas`: Used for CSV data handling.
  - `hypercorn`: The ASGI server used to run the FastAPI application.

---

This `README.md` now contains all the relevant details on how to use the API, including querying options and available headers. Let me know if you need further modifications!
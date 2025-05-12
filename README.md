<p align="center">
  <a href="https://nikshay-setu.in" target="_blank">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=200&color=gradient&text=Ni-kshay%20SETU&fontSize=50&fontAlign=50&fontAlignY=34" alt="Ni-kshay Setu banner"/>
  </a>
</p>

<p align="center">
  <a href="https://nikshay-setu.in/" target="_blank">
    <img src="https://nikshay-setu.in/newLogo.b72ac552416e2a050fc6c22c0491143e.svg" width="200" alt="Ni-kshay SETU" />
  </a>
</p>

<div align="center">

![Subscribers](https://img.shields.io/badge/Subscribers-44k%2B-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-GPL%203.0-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20Android%20%7C%20iOS-yellow?style=for-the-badge)
![Languages](https://img.shields.io/badge/Languages-8-orange?style=for-the-badge)

</div>

# Ni-Kshay SETU | Support to End TUberculosis

The Ni-kshay Setu app ([https://nikshay-setu.in/](https://nikshay-setu.in/)), already with **44K+ subscribers**, empowers healthcare providers to make informed decisions and contributes to India's mission to combat tuberculosis. Available on [web](https://nikshay-setu.in/), [Android](https://play.google.com/store/apps/details?id=com.iiphg.tbapp&pli=1), and [iOS](https://apps.apple.com/in/app/ni-kshay-setu/id1631331386) platforms in 8 languages, it offers real-time updates, interactive modules, and personalized insights, revolutionizing TB knowledge management and accessibility across India.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Features](#2-features)
3. [Technologies Used](#3-technologies-used)
4. [System Requirements](#4-system-requirements)
5. [Installation](#5-installation)
6. [Configuration](#6-configuration)
7. [Usage](#7-usage)
8. [Contribution Guidelines](#8-contribution-guidelines)
9. [License](#9-license)

## 1. Introduction

Ni-Kshay SETU is a groundbreaking digital solution available as a web application, Android application, and iOS application. With a mission to support healthcare providers in decision-making and transform knowledge into empowerment, this innovative and interactive learning tool is a catalyst in India's journey towards a TB-free nation.
As a comprehensive digital platform, Ni-Kshay SETU revolutionizes the way healthcare providers approach TB management. By leveraging cutting-edge technology, it empowers medical professionals with real-time support and evidence-based recommendations, ensuring they have the most up-to-date information at their fingertips.
With an intuitive interface and user-friendly design, Ni-Kshay SETU offers a seamless experience across devices, making it accessible to a wide range of users. The web application allows healthcare providers to access the platform from any computer, while the Android and iOS applications provide mobility and convenience for on-the-go professionals.
Through a range of interactive modules, virtual simulations, and case studies, Ni-Kshay SETU transforms learning into a dynamic and engaging experience. Healthcare providers can enhance their knowledge and skills by practicing TB case management in a risk-free environment. They can diagnose, prescribe treatment plans, and monitor patient progress, gaining invaluable experience and building their confidence in TB management.

> The Ni-Kshay SETU app is part of the 'Closing the Gaps in TB care Cascade (CGC)' project, developed by the Indian Institute of Public Health, Gandhinagar (https://iiphg.edu.in/). This project aims to strengthen health systems' ability to comprehensively monitor and respond to the TB care cascade with quality improvement (QI) interventions. This digital solution is one of the key interventions of the project with the objectives to strengthen the knowledge support system of the health staff in TB patient-centric care and program management of the National TB Elimination Program.

> Technological support for this project is provided by Digiflux Technologies Pvt. Ltd. (https://www.digiflux.io), contributing to the development and implementation of the digital solution.

IIPHG, The Union, and NTEP are proud partners in the development and implementation of Ni-Kshay SETU.

### 📊 Proactive Assessment System

**Proactive Assessment** is a Flask-based Python API application designed to dynamically generate and manage weekly assessments based on user preferences such as cadre, language, and number of assessments. The project ensures a unique and adaptive learning experience for users and is now open-sourced for the community!

## 2. Features

- 🎯 Personalized assessments based on cadre and language
- 🗓️ Weekly auto-generation of assessments based on user preference
- ✅ API to update user preferences
- 📥 API to submit assessment answers and track user performance
- 🔄 Reattempt mechanism for incorrectly answered questions
- 🧠 Ensures unique questions unless previously answered incorrectly

## 3. Technologies Used 

- **Language**: Python 3.10+ (Compatible with all later versions)
- **Framework**: Flask
- **Database**: Mongo DB
- **Task Scheduling**: Python Scheduler (e.g., APScheduler)

## 4. System Requirements

-   Operating System: Windows, Linux, macOS
-   Python 3.10+
-   Mongo DB


## 5. Installation

1. **Ensure Python and all dependencies are installed.**
   - Install **Python 3.10** or later.
   - Install all dependencies using:
     ```bash
     pip install -r requirements.txt
     ```

2. **Set up environment variables:**
   - Copy the example environment file and configure your environment variables:
     ```bash
     cp .env.example .env
     ```
   - Edit the `.env` file with appropriate values.

3. **Start the server using:**
   ```bash
   PYTHONPATH=. FLASK_APP=app/app.py FLASK_ENV=development flask run 
   ```

## 6. Configuration

The application requires certain configuration settings to work correctly. The main configuration file is `.env`. Update the following settings based on your environment:

| Variable Name                          | Description                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------|
| `MONGO_CLIENT`                        | MongoDB connection string used to connect to the database.                 |
| `MONGO_DB`                            | Name of the MongoDB database to be used.                                   |
| `DAY_OF_WEEK`                         | Day of the week to trigger scheduled tasks (e.g., `Monday`, `Tuesday`).    |
| `HOUR`                                | Hour at which scheduled tasks should run (0–23).                           |
| `MINUTES`                             | Minutes at which scheduled tasks should run (0–59).                        |
| `SLACK_WEBHOOK_URL`                   | Webhook URL for sending alerts or messages to Slack.                       |
| `APP_ENV`                             | Environment name (`development`, `staging`, `production`).                |
| `KMAP_COLLECTION`                     | MongoDB collection name for knowledge map data.                            |
| `PRIMARY_CADRE_COLLECTION`            | MongoDB collection for primary cadre-related data.                         |
| `CADRE_COLLECTION`                    | Collection for all cadres metadata.                                        |
| `QUESTIONS_COLLECTION`                | Collection storing assessment or quiz questions.                           |
| `ASSESSMENTS_COLLECTION`             | Collection storing assessment results and metadata.                        |
| `SUBSCRIBER_ACTIVITY_COLLECTION`      | Tracks user interactions or engagement.                                    |
| `ATTEMPT_LOG_COLLECTION`              | Stores logs of assessment attempts, including errors.                      |
| `USER_PREFERNCE_COLLECTION`           | Stores user-specific preferences for the application.                      |
| `PROASSESSMENT_RESPONSES_COLLECTION` | Stores responses from proactive assessments.                               |
| `PENDING_ASSESSMENTS_COUNT`           | Default number of pending assessments for a user.                          |
| `ASSESSMENT_COUNT`                    | Total number of assessments to be considered for a session.                |
| `DIFFICULTY_LEVELS`                   | Array of difficulty levels used to classify questions (e.g., Easy, Moderate, Hard). |
| `QUESTIONS_PER_ASSESSMENT`            | Number of questions to include in each assessment.                         |


## 7. Usage

### 📌 API Endpoints

#### 1. `POST /update_user_preferences`

Updates or sets the user’s assessment preferences.

#### Payload:

```json
{
  "user_id": "string",
  "cadre_id": "string",
  "lang": "string",
  "assessment_count": 0 to 7
}
```

- If `num_of_assessments` is `0`, the system defaults to generating 1 assessment.

- New users are added with preferences; existing users’ preferences are updated.

- A background scheduler (runs every Saturday at 11:00 PM) auto-generates assessments for the upcoming week based on stored preferences.

##

#### 2. `POST /update_assessment_submission`

Submits the user’s answers and calculates the score.

#### Payload:

```json
{
  "user_id": "string",
  "assessment_id": "string",
  "user_responses": [
    { "nid": "string", "user_answer": "string" },
    { "nid": "string", "user_answer": "string" },
    { "nid": "string", "user_answer": "string" },
    { "nid": "string", "user_answer": "string" },
    { "nid": "string", "user_answer": "string" }
  ]
}
```
 - Score is computed and stored.

 - If questions were answered incorrectly, they may appear again in future assessments until answered correctly.

### 🕒 Weekly Scheduler

A background job runs every **Saturday at 11:00 PM**, fetching all user preferences and generating assessments accordingly for the following week.

## 8. Contribution Guidelines

We welcome contributions from everyone! 🎉  
Please read our [CONTRIBUTING.md](CONTRIBUTING.md) guide to get started.  
If you find any issues or want to propose improvements, feel free to open an issue or a merge request.

## 9. License

Ni-kshay Setu project is licensed under the [GNU General Public License, Version 3.0](https://www.gnu.org/licenses/gpl-3.0).

![Static Badge](https://img.shields.io/badge/Licence-GPL%203.0-blue)



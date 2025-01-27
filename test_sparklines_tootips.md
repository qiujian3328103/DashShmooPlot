# **Critical ET & MSR Monitoring App Development Roadmap and Summary**

## **Summary:**
The Critical ET & MSR Monitoring App is a web-based platform designed to enable PE and YA engineers to monitor critical ET (parametric test) and MSR (EDS test item measurement) parameters. This application will automate the daily/hourly data querying process from the company’s data lake, apply user-defined rules (e.g., spec limits, control limits, sigma rules), and send automated alerts to engineers when abnormalities are detected. The app will feature a customizable frontend UI for rule management, parameter trend review, and inline data correlation, alongside robust backend processing and administrative controls for user permissions.

---

## **Development Roadmap:**

### **1. Project Planning and Requirements Gathering**

- **Duration:** 2 weeks
- **Tasks:**
  - Meet with PE department leaders and engineers to finalize requirements.
  - Document functional and non-functional requirements.
  - Outline the app’s architecture and key features (backend, frontend, database, notification system).
  - Identify technology stack (e.g., Python for backend, React/Vue.js for frontend, SQL for database).

### **2. Backend Development**

- **Duration:** 6 weeks
- **Tasks:**
  - **Data Query Module:**
    - Develop scripts to query ET/MSR data from the company’s data lake (Big Data Explorer).
    - Implement rule-based checks for abnormalities (spec limits, control limits, sigma rules).
  - **Alert System:**
    - Configure automated email notifications based on triggered rules.
    - Store notification logs in a database table.
  - **Data Storage:**
    - Design tables for summarized data (e.g., mean, std, median, spec, by lot/wafer).
    - Implement data saving mechanisms after each query.

### **3. Frontend UI Development**

- **Duration:** 6 weeks
- **Tasks:**
  - **Rule Management Interface:**
    - Develop a page for engineers to define and save rules for ET/MSR parameters.
    - Add options to select process ID, part ID, parameters, and rules.
  - **Trend Review and Correlation:**
    - Build a dashboard for visualizing parameter trends.
    - Enable correlation analysis with inline data.
  - **Spec Modification and Testing:**
    - Create a feature for users to test new rules and modify spec limits.
    - Include a wafer map selection for monitoring areas.
  - **Monitoring Activation/Deactivation:**
    - Allow users to activate or deactivate monitoring for specific parameters.

### **4. User and Admin Management**

- **Duration:** 3 weeks
- **Tasks:**
  - Implement user authentication and role-based access controls.
  - Develop admin features for managing user permissions (e.g., view-only, rule modification).
  - Create a user table to assign permissions and track activity.

### **5. Integration and Testing**

- **Duration:** 4 weeks
- **Tasks:**
  - **Integration:**
    - Integrate backend and frontend components.
    - Ensure seamless communication between the app and the data lake.
  - **Testing:**
    - Conduct unit testing for backend scripts and frontend components.
    - Perform end-to-end testing for all workflows (data querying, rule application, notifications, UI interactions).
    - Test user-defined rules in real scenarios with sample data.

### **6. Deployment and Training**

- **Duration:** 2 weeks
- **Tasks:**
  - Deploy the application on the company’s server or cloud platform.
  - Provide training sessions for PE and YA engineers.
  - Distribute user guides and documentation.

### **7. Post-Deployment Support and Maintenance**

- **Duration:** Ongoing
- **Tasks:**
  - Monitor app performance and resolve bugs.
  - Collect user feedback for future enhancements.
  - Regularly update the app to accommodate new requirements or improve features.

---

## **Key Features:**

1. **Automated Data Query and Alert System:**
   - Backend script to query ET/MSR data daily or hourly.
   - Rule-based alerting with email notifications.

2. **Customizable Rule Management:**
   - Frontend UI for selecting parameters, setting rules, and saving configurations.
   - Options to test and modify rules, including spec limits and activation status.

3. **Parameter Trend Review and Correlation:**
   - Interactive dashboards for trend visualization and correlation analysis.

4. **User and Admin Features:**
   - Role-based access control.
   - Admin capabilities for managing user permissions.

5. **Data Summary and Storage:**
   - Save summarized data (e.g., mean, std, median, by lot/wafer) in a local database.

---

## **Deliverables:**

- Fully functional Critical ET & MSR Monitoring App.
- Documentation: User guide, API documentation, and technical design documents.
- Training sessions for engineers.

---

In this project, I want to use the python dash as my backend and frontend. and sqlite3 as our database. We also going to use the companies big data explorer as our main query db, to query all the database data, may also needs some customized db to store the pre defined data such as the wafer map coordination, bin description, MSR naming, etc.

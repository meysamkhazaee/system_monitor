# **System Monitoring Script Setup and Execution**

expose resource usage of system and specific executable(memory, cpu and network)

## **2. Creating and Activating a New Virtual Environment**
- **Create a virtual environment**:
    ```bash
    python3 -m venv myvenv
    ```
- **Activate the virtual environment**:
    ```bash
    source myvenv/bin/activate
    ```

---

## **3. Installing Required Dependencies**
- **Install dependencies** using `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

### **Installed Packages**:
- `prometheus_client==0.20.0`
- `psutil==6.0.0`
- `colorlog==6.8.2`

---

## **4. Running the Monitoring Script**

### **First Attempt**
- **Run the script**:
    ```bash
    python3 main.py
    ```
- **Input**:
    - **Enter Process PIDs**: `10 20 30` or None for ignore process monitoring
    - **Enter Prometheus Client Port**: `9995`

---
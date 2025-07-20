import yaml
import os

def add_eco_ci_steps(yaml_data):
    modified_yaml_data = yaml_data.copy()
    
    if True in modified_yaml_data:
        modified_yaml_data['on'] = modified_yaml_data[True]
        del modified_yaml_data[True]
    
    for job_name, job in modified_yaml_data.get("jobs", {}).items():
        steps = job.setdefault("steps", [])
        
        steps.insert(0, {
            "name": "Start Energy Measurement",
            "uses": "green-coding-solutions/eco-ci-energy-estimation@v4",
            "with": {"task": "start-measurement", "json-output": True}
        })
        
        new_steps = []
        for step in steps:
            new_steps.append(step)
            if "run" in step:
                new_steps.append({
                    "name": f"Record Measurement After {step.get('name', 'Step')}",
                    "id": f"measurement-{len(new_steps)}",
                    "uses": "green-coding-solutions/eco-ci-energy-estimation@v4",
                    "with": {"task": "get-measurement", "label": step.get('name', 'Step'), "json-output": True}
                })
        
        new_steps.append({
            "name": "Display Energy Results",
            "id": "display-measurement",
            "uses": "green-coding-solutions/eco-ci-energy-estimation@v4",
            "with": {"task": "display-results", "json-output": True}
        })
        new_steps.append({
            "name": "Save Total Energy Consumption Data",
            "run": "echo '${{ steps.final-measurement.outputs.data-total-json }}' > total_energy_consumption.json"
        })
        new_steps.append({
            "name": "Upload Energy Consumption Artifact",
            "uses": "actions/upload-artifact@v4",
            "with": {"name": "total-energy-consumption", "path": "total_energy_consumption.json"}
        })
        
        job["steps"] = new_steps
    
    return modified_yaml_data

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

def write_yaml_with_header(file, data):
    file.write(f"name: {data['name']}\n")
    file.write("on:\n")
    file.write("  push:\n")
    file.write("    branches:\n")
    file.write("      - main\n\n")
    
    if 'name' in data:
        del data['name']
    if 'on' in data:
        del data['on']
    
    yaml.dump(data, file, Dumper=MyDumper, default_flow_style=False)

def process_all_yaml_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".yml") or filename.endswith(".yaml") :
            filepath = os.path.join(directory, filename)
            
            with open(filepath, "r") as file:
                yaml_data = yaml.safe_load(file)
            
            yaml_data = add_eco_ci_steps(yaml_data)
            
            with open(filepath, "w") as file:
                write_yaml_with_header(file, yaml_data)
            
            print(f"Modified YAML file saved as {filepath}")

workflow_directory = ".github/workflows/"
if os.path.exists(workflow_directory):
    process_all_yaml_files(workflow_directory)
else:
    print(f"Directory {workflow_directory} not found.")
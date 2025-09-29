import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
from typing import Dict, List
import re
import json


class ObjectData:
    def __init__(self, name: str, bone_id_counts: Dict[int, int]):
        self.name = name
        self.bone_id_counts = bone_id_counts
    
    def __repr__(self):
        return f"ObjectData(name='{self.name}', bone_id_counts={self.bone_id_counts})"

def extract_level_from_name(name: str) -> int:
    """
    Extract level number from object name (e.g., 'Trunk_L1' -> 1, 'Branch_L3' -> 3)
    
    Args:
        name: Object name containing level designation
    
    Returns:
        Level number as integer, or None if no level found
    """
    # Use regex to find L followed by digits
    match = re.search(r'_L(\d+)', name)
    if match:
        return int(match.group(1))
    return None

def parse_speedtree_xml(xml_content: str) -> Dict[int, List[ObjectData]]:
    """
    Parse SpeedTree XML and organize objects by level (1, 2, 3, etc.)
    
    Returns:
        Dictionary with level (int) as key and list of ObjectData as value
    """
    # Parse the XML
    root = ET.fromstring(xml_content)
    
    # Dictionary to store results organized by level
    level_data = defaultdict(list)
    
    # Find all objects
    objects = root.find('Objects')
    if objects is None:
        return {}
    
    for obj in objects.findall('Object'):
        name = obj.get('Name', '')
        
        # Extract level from name
        level = extract_level_from_name(name)
        
        print(f"Found Object: {name} at Level: {level}")
        # Skip objects without level designation
        if level is None:
            continue
        
        # Get vertices element to extract BoneID data
        vertices = obj.find('Vertices')
        print(f"Processing Object: {name}, Level: {level}")
        if vertices is not None:
            bone_id_element = vertices.find('BoneID')
            if bone_id_element is not None and bone_id_element.text:
                # Parse bone IDs and count occurrences
                bone_ids = []
                for bone_id_str in bone_id_element.text.strip().split():
                    try:
                        bone_id = int(bone_id_str)
                        if bone_id >= 0:  # Only count non-negative bone IDs
                            bone_ids.append(bone_id)
                    except ValueError:
                        continue  # Skip invalid bone ID values
                
                # Count occurrences of each bone ID
                bone_id_counts = dict(Counter(bone_ids))
            else:
                bone_id_counts = {}
        else:
            bone_id_counts = {}
        
        # Create ObjectData instance and add to appropriate level
        obj_data = ObjectData(name, bone_id_counts)
        level_data[level].append(obj_data)
    
    return dict(level_data)

# Read and parse the XML file
def read_speedtree_file(file_path: str) -> Dict[int, List[ObjectData]]:
    """Read SpeedTree XML file and return parsed data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
        return parse_speedtree_xml(xml_content)
    except FileNotFoundError:
        print(f"File {file_path} not found")
        return {}
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        return {}

def assign_bone_ids_to_levels(level_data: Dict[int, List[ObjectData]]) -> Dict[int, int]:
    """
    Assign bone IDs to their appropriate levels starting from highest level down to lowest.
    If a bone ID appears in lower levels, it's discarded from higher levels.
    
    Args:
        level_data: Dictionary with level (int) as key and list of ObjectData as value
    
    Returns:
        Dictionary with bone ID as key and level (int) as value
    """
    # Get all levels and sort from highest to lowest
    all_levels = sorted(level_data.keys(), reverse=True)
    
    if not all_levels:
        return {}
    
    print(f"Processing levels in order: {all_levels}")
    
    # Collect all bone IDs for each level
    level_bone_ids = {}
    for level in all_levels:
        bone_ids = set()
        for obj_data in level_data[level]:
            bone_ids.update(obj_data.bone_id_counts.keys())
        level_bone_ids[level] = bone_ids
        print(f"Level {level} has bone IDs: {sorted(bone_ids)}")
    
    # Dictionary to store final bone ID to level assignment
    bone_id_to_level = {}
    
    # Process levels from highest to lowest
    for i, current_level in enumerate(all_levels):
        current_bone_ids = level_bone_ids[current_level].copy()
        
        # Get all levels below current level
        lower_levels = all_levels[i + 1:]
        
        for bone_id in current_bone_ids:
            appears_in_lower = False
            
            # Check if this bone ID appears in any lower level
            for lower_level in lower_levels:
                if bone_id in level_bone_ids[lower_level]:
                    appears_in_lower = True
                    break
            
            # Only assign to current level if it doesn't appear in lower levels
            if not appears_in_lower:
                bone_id_to_level[bone_id] = current_level
                print(f"Bone ID {bone_id} assigned to level {current_level}")
            else:
                print(f"Bone ID {bone_id} discarded from level {current_level} (appears in lower levels)")
    
    return bone_id_to_level


def generate_wind_hierarchy_json(bone_assignments: Dict[int, int], output_path: str) -> None:
    """
    Generate a JSON file for wind hierarchy setup based on bone assignments.
    
    Args:
        bone_assignments: Dictionary with bone ID as key and level as value
        output_path: Path where to save the JSON file
    """
    if not bone_assignments:
        print("No bone assignments provided")
        return
    
    # Get all unique levels and sort them
    all_levels = sorted(set(bone_assignments.values()))
    max_level = max(all_levels)
    
    print(f"Found levels: {all_levels}, Max level: {max_level}")
    
    # Create joints list
    joints = []
    
    # Add Root joint (always simulation group 0)
    joints.append({
        "JointName": "Root",
        "SimulationGroupIndex": 0
    })
    
    # Add bone joints based on assignments
    for bone_id, level in sorted(bone_assignments.items()):
        # Calculate simulation group index (level - 1, but minimum 0)
        simulation_group_index = max(0, level - 1)
        
        # Add Start and End joints for each bone
        joints.extend([
            {
                "JointName": f"Bone_{bone_id}_Start",
                "SimulationGroupIndex": simulation_group_index
            },
            {
                "JointName": f"Bone_{bone_id}_End", 
                "SimulationGroupIndex": simulation_group_index
            }
        ])
    
    # Create simulation groups based on the number of levels
    simulation_groups = []
    
    # Group 0: Trunk group (for level 1 bones)
    simulation_groups.append({
        "bUseDualInfluence": False,
        "Influence": 1.0,
        "bIsTrunkGroup": True
    })
    
    # Additional groups for higher levels (level 2+)
    for level in range(2, max_level + 1):
        group_index = level - 1
        
        # Calculate influence values based on level
        # Higher levels have higher influence ranges
        min_influence = 0.2 + (group_index - 1) * 0.2
        max_influence = min(1.0, min_influence + 0.4)
        shift_top = max(0.0, 0.3 - (group_index - 1) * 0.1)
        
        simulation_groups.append({
            "bUseDualInfluence": True,
            "MinInfluence": round(min_influence, 2),
            "MaxInfluence": round(max_influence, 2),
            "ShiftTop": round(shift_top, 2),
            "bIsTrunkGroup": False
        })
    
    # Create the complete JSON structure
    wind_hierarchy = {
        "Joints": joints,
        "SimulationGroups": simulation_groups,
        "bIsGroundCover": False,
        "GustAttenuation": 0.25
    }
    
    # Write to JSON file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(wind_hierarchy, f, indent=2)
        
        print(f"\nWind hierarchy JSON saved to: {output_path}")
        print(f"Total joints: {len(joints)}")
        print(f"Total simulation groups: {len(simulation_groups)}")
        
        # Print summary
        print(f"\nSummary:")
        for i, group in enumerate(simulation_groups):
            bone_count = sum(1 for joint in joints if joint['SimulationGroupIndex'] == i and 'Start' in joint['JointName'])
            group_type = "Trunk" if group.get('bIsTrunkGroup', False) else "Branch"
            print(f"  Group {i} ({group_type}): {bone_count} bones")
            
    except Exception as e:
        print(f"Error writing JSON file: {e}")

def print_json_preview(bone_assignments: Dict[int, int]) -> None:
    """
    Print a preview of what the JSON structure would look like.
    """
    if not bone_assignments:
        print("No bone assignments to preview")
        return
        
    print("\nJSON Preview:")
    print("=" * 50)
    
    # Show some sample joints
    print("Sample Joints:")
    for bone_id in sorted(list(bone_assignments.keys())[:3]):  # Show first 3
        level = bone_assignments[bone_id]
        group_index = max(0, level - 1)
        print(f'  {{ "JointName": "Bone_{bone_id}_Start", "SimulationGroupIndex": {group_index} }}')
        print(f'  {{ "JointName": "Bone_{bone_id}_End", "SimulationGroupIndex": {group_index} }}')
    
    if len(bone_assignments) > 3:
        print(f"  ... and {(len(bone_assignments) - 3) * 2} more bone joints")
    
    # Show simulation groups
    levels = sorted(set(bone_assignments.values()))
    print(f"\nSimulation Groups ({len(levels)}):")
    for i, level in enumerate(levels):
        group_index = max(0, level - 1)
        is_trunk = level == 1
        print(f"  Group {group_index}: Level {level} ({'Trunk' if is_trunk else 'Branch'})")

# Add this to your existing execution code
if __name__ == "__main__":
    # Execute the existing code
    result = read_speedtree_file(r'path_to_your_file.xml')
    
    # Display results
    for level, objects in sorted(result.items()):
        print(f"\nLevel {level}:")
        for obj in objects:
            print(f"  {obj}")
    
    # Get bone ID to level assignments
    bone_assignments = assign_bone_ids_to_levels(result)
    
    print(f"\n\nBone ID Level Assignments:")
    print("=" * 40)
    for bone_id, level in sorted(bone_assignments.items()):
        print(f"Bone ID {bone_id}: Level {level}")
    
    # Preview the JSON structure
    print_json_preview(bone_assignments)
    
    # Generate the JSON file
    output_json_path = r'path_to_output_wind_hierarchy.json'
    generate_wind_hierarchy_json(bone_assignments, output_json_path)
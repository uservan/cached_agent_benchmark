import os
import yaml
from collections import defaultdict
from cached_datasets import load_dataset
from .. import BaseDataset, BaseTask, register_dataset

AGENT_SOLO_INSTRUCTION = """
You are a customer service agent that helps the user according to the <policy> provided below.
You will be provided with a ticket that contains the user's request.
You will need to plan and call the appropriate tools to solve the ticket.

You cannot communicate with the user, only make tool calls.
Stop when you consider that you have solved the ticket.
To do so, send a message containing a single tool call to the `{stop_function_name}` tool. Do not include any other tool calls in this last message.

Always follow the policy. Always make sure you generate valid JSON only.
""".strip()

SYSTEM_PROMPT_SOLO = """
<instructions>
{agent_instruction}
</instructions>
<policy>
{domain_policy}
</policy>
<ticket>
{ticket}
</ticket>
""".strip()

STOP_FUNCTION_NAME = "done"
TRANSFER_TOOL_NAME = "transfer_to_human_agents"
STOP_TOKEN = "###STOP###"



@register_dataset("tau2")
class Tau2Dataset(BaseDataset):
    def __init__(self, config_path=None):
        super().__init__(name='Tau2')
        
        # If no config path is specified, use the default config.yml
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
        
        # Load the config file
        self.config = self._load_config(config_path)
        
        # Load the dataset from HuggingFace
        self.tasks = self._load_and_assemble_tasks()
    
    def _load_config(self, config_path):
        """Load configuration from a YAML config file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    
    def _load_and_assemble_tasks(self):
        """Load the dataset from HuggingFace and assemble tasks"""
        hf_config = self.config.get('huggingface', {})
        task_config = self.config.get('task', {})
        
        # Load the task and response datasets
        task_ds = load_dataset(
            hf_config.get('task_dataset_name'),
            hf_config.get('task_config'),
            split=hf_config.get('task_split', 'train')
        )
        
        response_ds = load_dataset(
            hf_config.get('response_dataset_name'),
            hf_config.get('response_config'),
            split=hf_config.get('response_split', 'train')
        )
        
        # Build a response mapping (key: (dataset, domain, task), value: {tool_name: response})
        response_map = defaultdict(dict)
        for row in response_ds:
            key = (row.get('dataset'), row.get('domain'), row.get('task'))
            tool_name = row.get('tool')
            response_map[key][tool_name] = row.get('response')
        
        # Assemble the task list
        tasks = []
        for row in task_ds:
            key = (row.get('dataset'), row.get('domain'), row.get('task'))
            
            task_item = {
                'dataset': row.get('dataset'),
                'domain': row.get('domain'),
                'task': row.get('task'),
                'initial_state': row.get('initial_state', task_config.get('initial_state', {})),
                'tools': row.get('tools', task_config.get('tools', [])),
                'system_prompt': row.get('system_prompt', ''),
                'success_condition': row.get('success_condition', row.get('correct_answers', {})),
                'tool_responses': response_map.get(key, {}),
            }
            tasks.append(task_item)
        
        return tasks
    
    def load_data(self):
        """Return the loaded task data"""
        return self.tasks
    
    def __len__(self):
        return len(self.tasks)
    
    def __getitem__(self, idx):
        return self.tasks[idx]

class Tau2Task(BaseTask):
    def __init__(self, task_name, initial_state, tools, domain_policy):
        super().__init__(
            task_name=task_name,
            initial_state=initial_state,
            tools=tools
        )
        self.domain_policy = domain_policy
        # Other initialization logic

    def get_tool_schemas(self): 
        pass

    def get_user_prompt(self):
        return self.initial_state
    
    def is_finished(self, messages):
        # Determine whether the task is finished based on messages
        for msg in messages:
            if msg.get("role") == "tool" and msg.get("tool_name") == STOP_FUNCTION_NAME:
                return True
        return False

    def build_system_prompt(self):
        agent_instruction = AGENT_SOLO_INSTRUCTION.format(
            stop_function_name=STOP_FUNCTION_NAME,
            stop_token=STOP_TOKEN,
            )
        return SYSTEM_PROMPT_SOLO.format(
            agent_instruction=agent_instruction,
            domain_policy=self.domain_policy,
            ticket=self.initial_state,
        )

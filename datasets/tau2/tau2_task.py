import os
import yaml
from collections import defaultdict
from datasets import load_dataset
from .. import BaseDataset, BaseTask, register_dataset

@register_dataset("tau2")
class Tau2Dataset(BaseDataset):
    def __init__(self, config_path=None):
        super().__init__(name='Tau2')
        
        # 如果没有指定配置路径，使用默认的 config.yml
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
        
        # 加载配置文件
        self.config = self._load_config(config_path)
        
        # 从 HuggingFace 加载数据集
        self.tasks = self._load_and_assemble_tasks()
    
    def _load_config(self, config_path):
        """从 YAML 配置文件加载配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    
    def _load_and_assemble_tasks(self):
        """从 HuggingFace 加载数据集并组装任务"""
        hf_config = self.config.get('huggingface', {})
        task_config = self.config.get('task', {})
        
        # 加载任务和响应数据集
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
        
        # 构建响应映射（key: (dataset, domain, task), value: {tool_name: response}）
        response_map = defaultdict(dict)
        for row in response_ds:
            key = (row.get('dataset'), row.get('domain'), row.get('task'))
            tool_name = row.get('tool')
            response_map[key][tool_name] = row.get('response')
        
        # 组装任务列表
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
        """返回已加载的任务数据"""
        return self.tasks
    
    def __len__(self):
        return len(self.tasks)
    
    def __getitem__(self, idx):
        return self.tasks[idx]

class Tau2Task(BaseTask):
    def __init__(self, initial_state, tools):
        super().__init__(
            dataset=Tau2Dataset(),
            domain='tau2',
            task_name='Tau2 Task',
            initial_state=initial_state,
            tools=tools
        )
        # 其他初始化逻辑

"""测试JSON修复功能"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.utils import validate_json_output

# 测试用例1: 包含无效转义字符的JSON
test_json_1 = '''{
  "credibility_score": 1.0,
  "is_valid": true,
  "evidence": [
    {
      "source": "Britannica",
      "snippet": "entropy is a measure of 'disorder' (the higher the entropy)"
    }
  ]
}'''

# 测试用例2: 包含 \e 等无效转义的JSON
test_json_2 = '''{
  "text": "This has invalid \\escape sequence"
}'''

# 测试用例3: 正常的JSON
test_json_3 = '''{
  "name": "test",
  "value": 123
}'''

print("测试1: 正常JSON")
try:
    result = validate_json_output(test_json_3)
    print(f"✓ 成功: {result}")
except Exception as e:
    print(f"✗ 失败: {e}")

print("\n测试2: 包含单引号的JSON")
try:
    result = validate_json_output(test_json_1)
    print(f"✓ 成功: {result}")
except Exception as e:
    print(f"✗ 失败: {e}")

print("\n测试3: 包含无效转义的JSON")
try:
    result = validate_json_output(test_json_2)
    print(f"✓ 成功: {result}")
except Exception as e:
    print(f"✗ 失败: {e}")

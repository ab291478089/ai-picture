from flask import Flask, request, jsonify, send_from_directory
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')

ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY', '')
ZHIPU_API_BASE = 'https://open.bigmodel.cn/api/paas/v4'


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    size = data.get('size', '1024x1024')
    style = data.get('style', 'vivid')

    if not ZHIPU_API_KEY:
        return jsonify({'error': '未配置 ZHIPU_API_KEY，请在 .env 文件中设置'}), 500

    if not prompt.strip():
        return jsonify({'error': '请输入图片描述'}), 400

    style_prefix = ''
    if style == 'vivid':
        style_prefix = '高质量、生动鲜艳、细节丰富、光影效果强烈：'
    elif style == 'natural':
        style_prefix = '自然写实、柔和光线、真实质感：'

    full_prompt = style_prefix + prompt

    headers = {
        'Authorization': f'Bearer {ZHIPU_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': 'cogview-3-flash',
        'prompt': full_prompt,
        'size': size
    }

    try:
        response = requests.post(
            f'{ZHIPU_API_BASE}/images/generations',
            headers=headers,
            json=payload,
            timeout=120
        )
        result = response.json()

        if response.status_code != 200:
            error_msg = result.get('error', {}).get('message', '生成失败')
            return jsonify({'error': error_msg}), response.status_code

        return jsonify(result)
    except requests.exceptions.Timeout:
        return jsonify({'error': '请求超时，请稍后重试'}), 504
    except Exception as e:
        return jsonify({'error': f'服务异常：{str(e)}'}), 500


@app.route('/api/optimize', methods=['POST'])
def optimize():
    data = request.json
    prompt = data.get('prompt', '')

    if not ZHIPU_API_KEY:
        return jsonify({'error': '未配置 ZHIPU_API_KEY，请在 .env 文件中设置'}), 500

    if not prompt.strip():
        return jsonify({'error': '请输入图片描述'}), 400

    headers = {
        'Authorization': f'Bearer {ZHIPU_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': 'glm-4-flash',
        'messages': [
            {
                'role': 'system',
                'content': '你是一个AI图片提示词优化专家。请将用户提供的简短图片描述优化为更详细、更具画面感的英文提示词，用于AI图片生成。优化要求：1.添加具体的视觉细节（光影、色彩、构图）2.添加风格描述（如cinematic、8K、hyper-detailed等）3.只返回优化后的提示词文本，不要任何解释或前缀'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    try:
        response = requests.post(
            f'{ZHIPU_API_BASE}/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        result = response.json()

        if response.status_code != 200:
            error_msg = result.get('error', {}).get('message', '优化失败')
            return jsonify({'error': error_msg}), response.status_code

        optimized = result['choices'][0]['message']['content']
        return jsonify({'optimized_prompt': optimized})
    except requests.exceptions.Timeout:
        return jsonify({'error': '请求超时，请稍后重试'}), 504
    except Exception as e:
        return jsonify({'error': f'服务异常：{str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080)

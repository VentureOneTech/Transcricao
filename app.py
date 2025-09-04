#!/usr/bin/env python3
"""
Flask App para Transcrição de Áudio
Versão web do assemblyai_final_working.py
"""

import os
import time
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import threading

# Importar o módulo de transcrição
from transcription_service import TranscriptionService

# Configurar Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'

# Criar diretórios
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instância do serviço de transcrição
transcription_service = TranscriptionService()

# Armazenar status dos jobs
jobs_status = {}

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint para upload de arquivo"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        # Verificar extensão
        allowed_extensions = {'mp3', 'wav', 'm4a', 'flac', 'aac', 'ogg', 'opus'}
        if not file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
            return jsonify({'error': 'Formato de arquivo não suportado'}), 400
        
        # Salvar arquivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Criar job ID
        job_id = str(uuid.uuid4())
        jobs_status[job_id] = {
            'status': 'uploaded',
            'filename': filename,
            'filepath': filepath,
            'progress': 0,
            'message': 'Arquivo enviado com sucesso',
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Arquivo enviado: {filename} -> {filepath}")
        
        return jsonify({
            'job_id': job_id,
            'filename': filename,
            'message': 'Arquivo enviado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe/<job_id>', methods=['POST'])
def start_transcription(job_id):
    """Iniciar transcrição em background"""
    try:
        if job_id not in jobs_status:
            return jsonify({'error': 'Job não encontrado'}), 404
        
        job = jobs_status[job_id]
        if job['status'] != 'uploaded':
            return jsonify({'error': 'Job já processado'}), 400
        
        # Atualizar status
        job['status'] = 'processing'
        job['progress'] = 0
        job['message'] = 'Iniciando transcrição...'
        
        # Iniciar transcrição em thread separada
        thread = threading.Thread(target=process_transcription, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Transcrição iniciada'
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar transcrição: {e}")
        return jsonify({'error': str(e)}), 500

def process_transcription(job_id):
    """Processar transcrição em background"""
    try:
        job = jobs_status[job_id]
        filepath = job['filepath']
        
        # Atualizar progresso
        job['progress'] = 10
        job['message'] = 'Convertendo arquivo...'
        
        # Processar transcrição
        result = transcription_service.transcribe_audio(filepath, job)
        
        if result['success']:
            job['status'] = 'completed'
            job['progress'] = 100
            job['message'] = 'Transcrição concluída!'
            job['result_file'] = result['transcript_file']
            job['language_code'] = result.get('language_code')
            job['completed_at'] = datetime.now().isoformat()
        else:
            job['status'] = 'error'
            job['message'] = f"Erro: {result['error']}"
            
    except Exception as e:
        logger.error(f"Erro na transcrição: {e}")
        job['status'] = 'error'
        job['message'] = f"Erro interno: {str(e)}"

@app.route('/status/<job_id>')
def get_status(job_id):
    """Obter status do job"""
    if job_id not in jobs_status:
        return jsonify({'error': 'Job não encontrado'}), 404
    
    job = jobs_status[job_id]
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'message': job['message'],
        'filename': job['filename'],
        'result_file': job.get('result_file'),
        'language_code': job.get('language_code'),
        'created_at': job['created_at'],
        'completed_at': job.get('completed_at')
    })

@app.route('/download/<job_id>')
def download_result(job_id):
    """Download do arquivo de transcrição"""
    if job_id not in jobs_status:
        return jsonify({'error': 'Job não encontrado'}), 404
    
    job = jobs_status[job_id]
    if job['status'] != 'completed':
        return jsonify({'error': 'Transcrição não concluída'}), 400
    
    result_file = job['result_file']
    if not os.path.exists(result_file):
        return jsonify({'error': 'Arquivo não encontrado'}), 404
    
    # Nome do arquivo para download
    download_name = f"{Path(job['filename']).stem}_transcricao.txt"
    
    return send_file(
        result_file,
        as_attachment=True,
        download_name=download_name,
        mimetype='text/plain'
    )

@app.route('/health')
def health_check():
    """Health check para Render"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

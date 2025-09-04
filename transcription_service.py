#!/usr/bin/env python3
"""
Serviço de Transcrição
Baseado no assemblyai_final_working.py
"""

import os
import sys
import time
import logging
import subprocess
import requests
from pathlib import Path
from tqdm import tqdm
import urllib.request
import urllib.parse
from datetime import datetime

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self):
        # Formatos suportados
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg']
        self.output_dir = "results"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # API key do AssemblyAI - PEGAR DO AMBIENTE
        self.api_key = os.environ.get('ASSEMBLYAI_API_KEY')
        if not self.api_key:
            logger.error("❌ ASSEMBLYAI_API_KEY não encontrada nas variáveis de ambiente!")
            raise ValueError("ASSEMBLYAI_API_KEY não configurada")
        
        # URL da API
        self.upload_url = "https://api.assemblyai.com/v2/upload"
        self.transcribe_url = "https://api.assemblyai.com/v2/transcript"
        
        # Headers
        self.headers = {
            "authorization": self.api_key,
            "content-type": "application/json"
        }
    
    def convert_to_mp3(self, input_file):
        """Converte arquivo para MP3 otimizado para AssemblyAI"""
        try:
            input_path = Path(input_file)
            output_file = input_path.with_suffix('.mp3')
            
            logger.info(f"🔄 Convertendo {input_path.name} para MP3...")
            
            # Comando FFmpeg otimizado para AssemblyAI
            cmd = [
                'ffmpeg', '-i', str(input_path),
                '-ar', '16000',      # 16kHz sample rate
                '-ac', '1',          # Mono
                '-b:a', '128k',      # 128kbps bitrate
                '-y',                # Sobrescrever se existir
                str(output_file)
            ]
            
            # Executar conversão com barra de progresso
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Simular progresso baseado no tempo
            start_time = time.time()
            while process.poll() is None:
                elapsed = time.time() - start_time
                progress = min(int(elapsed * 10), 90)  # Máximo 90% durante conversão
                yield progress
                time.sleep(0.1)
            
            if process.returncode == 0:
                logger.info(f"✅ Conversão concluída: {output_file.name}")
                yield 100
                return str(output_file)
            else:
                logger.error("❌ Erro na conversão")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro na conversão: {e}")
            return None
    
    def upload_file(self, file_path, job_status=None):
        """Upload do arquivo para AssemblyAI"""
        try:
            logger.info("📤 Enviando arquivo para AssemblyAI...")
            
            # Abrir arquivo
            with open(file_path, "rb") as f:
                response = requests.post(
                    self.upload_url,
                    headers=self.headers,
                    data=f,
                    stream=True
                )
            
            if response.status_code == 200:
                upload_url = response.json()["upload_url"]
                logger.info("✅ Arquivo enviado com sucesso!")
                
                # Atualizar progresso final do upload
                if job_status:
                    job_status['progress'] = 50
                    job_status['message'] = 'Upload concluído! Iniciando transcrição...'
                
                return upload_url
            else:
                logger.error(f"❌ Erro no upload: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro no upload: {e}")
            return None
    
    def transcribe_audio_api(self, upload_url, job_status=None):
        """Transcrever áudio usando AssemblyAI"""
        try:
            logger.info("⏳ Iniciando transcrição...")
            
            # Configuração da transcrição
            transcript_request = {
                "audio_url": upload_url,
                "boost_param": "high",  # Boost de qualidade
                "speaker_labels": True,  # Identificar falantes
                "punctuate": True,       # Pontuação
                "format_text": True,     # Formatar texto
                "language_detection": True  # Detecção automática de idioma
            }
            
            # Enviar requisição de transcrição
            if job_status:
                job_status['progress'] = 55
                job_status['message'] = 'Iniciando transcrição...'
            
            response = requests.post(
                self.transcribe_url,
                json=transcript_request,
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Erro na requisição: {response.status_code}")
                return None
            
            transcript_id = response.json()["id"]
            logger.info(f"📋 ID da transcrição: {transcript_id}")
            
            # Aguardar conclusão com progresso real
            max_attempts = 60  # Máximo 5 minutos (60 * 5 segundos)
            last_status = None
            attempts = 0
            start_time = time.time()
            
            while attempts < max_attempts:
                polling_response = requests.get(
                    f"{self.transcribe_url}/{transcript_id}",
                    headers=self.headers
                )
                
                if polling_response.status_code != 200:
                    logger.error(f"❌ Erro no polling: {polling_response.status_code}")
                    return None
                
                polling_response = polling_response.json()
                status = polling_response["status"]
                
                # Calcular progresso baseado no tempo e status
                elapsed_time = time.time() - start_time
                base_progress = 55  # Começa em 55%
                
                if status == "queued":
                    progress = base_progress + min(int(elapsed_time * 2), 10)  # 55-65%
                    message = "Aguardando na fila..."
                elif status == "processing":
                    progress = base_progress + 10 + min(int(elapsed_time * 3), 25)  # 65-90%
                    message = "Processando transcrição..."
                else:
                    progress = base_progress + 35
                    message = "Finalizando..."
                
                # Atualizar progresso
                if job_status:
                    job_status['progress'] = min(progress, 90)
                    job_status['message'] = message
                
                # Log apenas mudanças de status importantes
                if attempts == 0 or status != last_status:
                    logger.info(f"📊 Status da transcrição: {status}")
                    last_status = status
                
                if status == "completed":
                    logger.info("✅ Transcrição concluída!")
                    if job_status:
                        job_status['progress'] = 95
                        job_status['message'] = 'Transcrição concluída!'
                    return polling_response
                elif status == "error":
                    logger.error(f"❌ Erro na transcrição: {polling_response.get('error')}")
                    return None
                
                # Aguardar antes de verificar novamente
                time.sleep(5)
                attempts += 1
            
            logger.error("❌ Timeout: Transcrição demorou muito para completar")
            return None
                
        except Exception as e:
            logger.error(f"❌ Erro na transcrição: {e}")
            return None
    
    def save_transcript(self, transcript_data, original_filename):
        """Salvar transcrição em arquivo"""
        try:
            # Nome do arquivo de saída
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{timestamp}_{Path(original_filename).stem}_transcript.txt"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Extrair texto da transcrição
            text = transcript_data.get("text", "")
            utterances = transcript_data.get("utterances", [])
            
            # Criar conteúdo formatado
            content = "=== TRANSCRIÇÃO ASSEMBLYAI ===\n\n"
            
            # Informações gerais
            if "language_code" in transcript_data:
                content += f"Idioma detectado: {transcript_data['language_code']}\n"
            if "confidence" in transcript_data:
                content += f"Confiança: {transcript_data['confidence']:.2f}\n"
            if utterances:
                content += f"Total de falantes: {len(set(u.get('speaker', 'A') for u in utterances))}\n"
            
            content += "\n=== SEGMENTOS COM FALANTES ===\n\n"
            
            # Ordenar utterances por tempo de início
            utterances_sorted = sorted(utterances, key=lambda x: x.get("start", 0))
            
            # Adicionar segmentos com falantes
            for utterance in utterances_sorted:
                start = utterance.get("start", 0)
                end = utterance.get("end", 0)
                
                # DEBUG: Log dos valores brutos da API
                logger.info(f"DEBUG RAW: start={start}, end={end}, speaker={utterance.get('speaker', 'A')}")
                
                # Converter segundos para formato HH:MM:SS correto
                start_hours = int(start // 3600)
                start_minutes = int((start % 3600) // 60)
                start_seconds = int(start % 60)
                
                end_hours = int(end // 3600)
                end_minutes = int((end % 3600) // 60)
                end_seconds = int(end % 60)
                
                # Formato HH:MM:SS
                start_time = f"{start_hours:02d}:{start_minutes:02d}:{start_seconds:02d}"
                end_time = f"{end_hours:02d}:{end_minutes:02d}:{end_seconds:02d}"
                speaker = utterance.get("speaker", "A")
                text_segment = utterance.get("text", "")
                
                content += f"[{start_time} - {end_time}] Speaker {speaker}: {text_segment}\n\n"
            
            # Salvar arquivo
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"✅ Transcrição salva: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar transcrição: {e}")
            return None
    
    def transcribe_audio(self, file_path, job_status=None):
        """Método principal para transcrição"""
        try:
            # Verificar se precisa converter
            input_path = Path(file_path)
            if input_path.suffix.lower() in ['.m4a', '.aac', '.ogg', '.opus']:
                logger.info(f"🔄 Convertendo {input_path.suffix} para MP3")
                
                # Converter para MP3
                converted_file = None
                for progress in self.convert_to_mp3(file_path):
                    if job_status:
                        job_status['progress'] = 10 + int(progress * 0.3)  # 10-40%
                        job_status['message'] = f'Convertendo arquivo... {progress}%'
                        time.sleep(0.1)  # Pequena pausa para atualizar UI
                
                converted_file = input_path.with_suffix('.mp3')
                if not converted_file.exists():
                    return {'success': False, 'error': 'Falha na conversão'}
                
                process_file = str(converted_file)
            else:
                process_file = file_path
            
            # Upload do arquivo
            if job_status:
                job_status['progress'] = 40
                job_status['message'] = 'Enviando arquivo...'
            
            upload_url = self.upload_file(process_file, job_status)
            if not upload_url:
                return {'success': False, 'error': 'Falha no upload'}
            
            # Transcrever
            if job_status:
                job_status['progress'] = 50
                job_status['message'] = 'Processando transcrição...'
            
            transcript_data = self.transcribe_audio_api(upload_url, job_status)
            if not transcript_data:
                return {'success': False, 'error': 'Falha na transcrição'}
            
            # Salvar resultado
            if job_status:
                job_status['progress'] = 95
                job_status['message'] = 'Salvando resultado...'
            
            result_file = self.save_transcript(transcript_data, input_path.name)
            if not result_file:
                return {'success': False, 'error': 'Falha ao salvar transcrição'}
            
            # Limpar arquivo convertido se necessário
            if input_path.suffix.lower() in ['.m4a', '.aac', '.ogg', '.opus']:
                try:
                    converted_file.unlink()
                except:
                    pass
            
            # Calcular número de interlocutores
            utterances = transcript_data.get('utterances', [])
            speakers_count = len(set(u.get('speaker', 'A') for u in utterances)) if utterances else 0
            
            # Progresso final
            if job_status:
                job_status['progress'] = 100
                job_status['message'] = 'Transcrição concluída com sucesso!'
            
            return {
                'success': True,
                'transcript_file': result_file,
                'language_code': transcript_data.get('language_code'),
                'speakers_count': speakers_count,
                'message': 'Transcrição concluída com sucesso!'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            return {'success': False, 'error': str(e)}
# FORÇAR MUDANÇA CRÍTICA Wed Sep  3 21:56:13 -05 2025

from flask import Flask, render_template, jsonify, request
import asyncio
import logging
import time
from aiokef import AsyncKefSpeaker
from functools import wraps
from werkzeug.serving import WSGIRequestHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom request handler to control access logging
class CustomRequestHandler(WSGIRequestHandler):
    # Track last status log time as a class variable
    last_status_log = 0
    
    def log_request(self, code='-', size='-'):
        # Check if this is a status endpoint request
        if self.path == '/api/status':
            current_time = time.time()
            # Only log if 1 minute (60 seconds) has passed
            if current_time - CustomRequestHandler.last_status_log >= 60:
                CustomRequestHandler.last_status_log = current_time
                super().log_request(code, size)
        else:
            # Log all other requests normally
            super().log_request(code, size)

app = Flask(__name__)

# Create speaker instance
SPEAKER_IP = '192.168.4.47'
speaker = AsyncKefSpeaker(SPEAKER_IP)

# Create a new event loop for the Flask application
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def run_async(coro):
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error in async operation: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

# Track last endpoint log time
last_endpoint_log = 0

def log_endpoint(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            global last_endpoint_log
            current_time = time.time()
            
            # Only log status endpoint with time filtering
            if f.__name__ == 'get_status':
                # Only log if 1 minute (60 seconds) has passed
                if current_time - last_endpoint_log >= 60:
                    last_endpoint_log = current_time
                    logger.info(f"Calling endpoint {f.__name__}")
                    result = f(*args, **kwargs)
                    logger.info(f"Endpoint {f.__name__} completed successfully")
                    print(result)
                    return result
                else:
                    # Just execute without logging if within time window
                    return f(*args, **kwargs)
            else:
                # Log all other endpoints normally
                logger.info(f"Calling endpoint {f.__name__}")
                result = f(*args, **kwargs)
                logger.info(f"Endpoint {f.__name__} completed successfully")
                print(result)
                return result
        except Exception as e:
            logger.error(f"Error in endpoint {f.__name__}: {str(e)}")
            raise
    return wrapper

@app.route('/api/status')
@log_endpoint
def get_status():
    try:
        # Check if speaker is online first
        if not run_async(speaker.is_online()):
            logger.error("Speaker is offline")
            return jsonify({
                'success': False,
                'error': 'Speaker is offline'
            })

        # Get all status information
        state = run_async(speaker.get_state())
        logger.debug(f"Speaker state: {state}")
        
        volume = run_async(speaker.get_volume())
        logger.debug(f"Speaker volume: {volume}")
        
        source = run_async(speaker.get_source())
        logger.debug(f"Speaker source: {source}")
        
        mode = run_async(speaker.get_mode())
        logger.debug(f"Speaker mode: {mode}")
        return jsonify({
            'state': state,
            'volume': volume,
            'source': source,
            'mode': mode,
            'success': True
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/control/<command>', methods=['POST'])
@log_endpoint
def control(command):
    # Check if speaker is online first
    if not run_async(speaker.is_online()):
        logger.error("Speaker is offline")
        return jsonify({
            'success': False,
            'error': 'Speaker is offline'
        })
    try:
        if command == 'turn_on':
            run_async(speaker.turn_on())
        elif command == 'turn_off':
            run_async(speaker.turn_off())
        elif command == 'mute':
            run_async(speaker.mute())
        elif command == 'unmute':
            run_async(speaker.unmute())
        elif command == 'volume_up':
            run_async(speaker.increase_volume())
        elif command == 'volume_down':
            run_async(speaker.decrease_volume())
        elif command == 'set_volume':
            volume = float(request.json['value'])
            run_async(speaker.set_volume(volume))
        elif command == 'set_source':
            source = request.json['value']
            run_async(speaker.set_source(source))
        else:
            return jsonify({'success': False, 'error': 'Unknown command'})
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application...")
        logger.info(f"Speaker IP: {SPEAKER_IP}")
        # Check if speaker is online before starting
        if not run_async(speaker.is_online()):
            logger.error("Speaker is offline. Please check the connection.")
            exit(1)
        logger.info("Speaker is online. Starting web server...")
        # Use custom request handler
        app.run(host='0.0.0.0', port=50000, request_handler=CustomRequestHandler)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        exit(1)
    finally:
        loop.close()

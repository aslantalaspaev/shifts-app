from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import SessionLocal, User, Shift, ShiftRequest, ShiftHistory
import json

app = Flask(__name__)
CORS(app)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_telegram_data(data):
    """Проверяет подпись Telegram Mini App"""
    # В продакшене нужно проверять подпись
    return True

@app.route('/api/auth', methods=['POST'])
def auth():
    """Авторизация пользователя"""
    data = request.json
    telegram_id = str(data.get('telegram_id'))
    ldap = data.get('ldap', '')
    first_name = data.get('first_name', '')
    username = data.get('username', '')
    
    if not telegram_id or not ldap:
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = next(get_db())
    
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            ldap=ldap,
            first_name=first_name,
            username=username
        )
        db.add(user)
    else:
        user.ldap = ldap
        user.first_name = first_name
        user.username = username
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'user_id': telegram_id})

@app.route('/api/available-shifts', methods=['GET'])
def available_shifts():
    """Получить все доступные смены"""
    db = next(get_db())
    
    shifts = db.query(Shift).filter(Shift.is_active == True).all()
    
    result = []
    for shift in shifts:
        creator = db.query(User).filter(User.telegram_id == shift.creator_telegram_id).first()
        
        # Проверяем статус запроса на эту смену
        request_status = db.query(ShiftRequest).filter(
            ShiftRequest.shift_id == shift.id,
            ShiftRequest.status == 'approved'
        ).first()
        
        is_taken = request_status is not None
        
        shift_info = {
            'id': shift.id,
            'creator_ldap': creator.ldap if creator else 'Unknown',
            'creator_name': creator.first_name if creator else 'Unknown',
            'shift_date': shift.shift_date,
            'shift_type': shift.shift_type,
            'start_time': shift.start_time,
            'end_time': shift.end_time,
            'is_taken': is_taken,
            'requester_ldap': None,
            'created_at': shift.created_at.isoformat() if shift.created_at else None
        }
        
        if is_taken:
            requester = db.query(User).filter(User.telegram_id == request_status.requester_telegram_id).first()
            shift_info['requester_ldap'] = requester.ldap if requester else 'Unknown'
        
        result.append(shift_info)
    
    db.close()
    return jsonify(result)

@app.route('/api/shift/create', methods=['POST'])
def create_shift():
    """Создать новую смену"""
    data = request.json
    telegram_id = str(data.get('telegram_id'))
    shift_date = data.get('shift_date')
    shift_type = data.get('shift_type')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    
    if not all([telegram_id, shift_date, shift_type]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    db = next(get_db())
    
    shift = Shift(
        creator_telegram_id=telegram_id,
        shift_date=shift_date,
        shift_type=shift_type,
        start_time=start_time,
        end_time=end_time
    )
    
    db.add(shift)
    db.commit()
    
    # Добавляем в историю
    history = ShiftHistory(
        shift_id=shift.id,
        creator_telegram_id=telegram_id,
        action='created',
        shift_date=shift_date,
        shift_type=shift_type
    )
    db.add(history)
    db.commit()
    
    db.close()
    return jsonify({'success': True, 'shift_id': shift.id})

@app.route('/api/shift/request', methods=['POST'])
def request_shift():
    """Запросить смену"""
    data = request.json
    shift_id = data.get('shift_id')
    requester_telegram_id = str(data.get('telegram_id'))
    
    db = next(get_db())
    
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        db.close()
        return jsonify({'error': 'Shift not found'}), 404
    
    # Проверяем, не запрашивал ли уже этот пользователь эту смену
    existing_request = db.query(ShiftRequest).filter(
        ShiftRequest.shift_id == shift_id,
        ShiftRequest.requester_telegram_id == requester_telegram_id
    ).first()
    
    if existing_request:
        db.close()
        return jsonify({'error': 'Already requested'}), 400
    
    shift_request = ShiftRequest(
        shift_id=shift_id,
        requester_telegram_id=requester_telegram_id,
        creator_telegram_id=shift.creator_telegram_id,
        status='pending'
    )
    
    db.add(shift_request)
    db.commit()
    
    db.close()
    return jsonify({'success': True, 'request_id': shift_request.id})

@app.route('/api/shift/requests', methods=['GET'])
def get_requests():
    """Получить все запросы для смен текущего пользователя"""
    telegram_id = request.args.get('telegram_id')
    
    db = next(get_db())
    
    requests = db.query(ShiftRequest).filter(
        ShiftRequest.creator_telegram_id == telegram_id
    ).all()
    
    result = []
    for req in requests:
        shift = db.query(Shift).filter(Shift.id == req.shift_id).first()
        requester = db.query(User).filter(User.telegram_id == req.requester_telegram_id).first()
        
        result.append({
            'id': req.id,
            'shift_id': req.shift_id,
            'shift_date': shift.shift_date if shift else None,
            'shift_type': shift.shift_type if shift else None,
            'requester_ldap': requester.ldap if requester else 'Unknown',
            'requester_name': requester.first_name if requester else 'Unknown',
            'status': req.status,
            'created_at': req.created_at.isoformat() if req.created_at else None
        })
    
    db.close()
    return jsonify(result)

@app.route('/api/shift/approve', methods=['POST'])
def approve_shift():
    """Подтвердить запрос на смену"""
    data = request.json
    request_id = data.get('request_id')
    
    db = next(get_db())
    
    shift_request = db.query(ShiftRequest).filter(ShiftRequest.id == request_id).first()
    if not shift_request:
        db.close()
        return jsonify({'error': 'Request not found'}), 404
    
    # Отклоняем все остальные запросы на эту смену
    db.query(ShiftRequest).filter(
        ShiftRequest.shift_id == shift_request.shift_id,
        ShiftRequest.id != request_id,
        ShiftRequest.status == 'pending'
    ).update({'status': 'rejected'})
    
    shift_request.status = 'approved'
    db.commit()
    
    shift = db.query(Shift).filter(Shift.id == shift_request.shift_id).first()
    shift.is_active = False
    db.commit()
    
    db.close()
    return jsonify({'success': True})

@app.route('/api/shift/reject', methods=['POST'])
def reject_shift():
    """Отклонить запрос на смену"""
    data = request.json
    request_id = data.get('request_id')
    
    db = next(get_db())
    
    shift_request = db.query(ShiftRequest).filter(ShiftRequest.id == request_id).first()
    if not shift_request:
        db.close()
        return jsonify({'error': 'Request not found'}), 404
    
    shift_request.status = 'rejected'
    db.commit()
    
    db.close()
    return jsonify({'success': True})

@app.route('/api/shift/history', methods=['GET'])
def shift_history():
    """Получить историю смен"""
    telegram_id = request.args.get('telegram_id')
    
    db = next(get_db())
    
    history = db.query(ShiftHistory).filter(
        (ShiftHistory.creator_telegram_id == telegram_id) |
        (ShiftHistory.requester_telegram_id == telegram_id)
    ).order_by(ShiftHistory.created_at.desc()).limit(100).all()
    
    result = []
    for h in history:
        creator = db.query(User).filter(User.telegram_id == h.creator_telegram_id).first()
        requester = db.query(User).filter(User.telegram_id == h.requester_telegram_id).first() if h.requester_telegram_id else None
        
        result.append({
            'id': h.id,
            'creator_ldap': creator.ldap if creator else 'Unknown',
            'requester_ldap': requester.ldap if requester else None,
            'action': h.action,
            'shift_date': h.shift_date,
            'shift_type': h.shift_type,
            'created_at': h.created_at.isoformat() if h.created_at else None
        })
    
    db.close()
    return jsonify(result)

@app.route('/')
def index():
    """Главная страница Mini App"""
    return render_template('index.html', mini_app_url=MINI_APP_URL)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

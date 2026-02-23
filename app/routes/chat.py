from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app import db, socketio
from app.models.chat import Conversation, Message
from app.models import Listing
from flask_socketio import emit, join_room
from datetime import datetime

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/')
@login_required
def index():
    conversations = Conversation.query.filter((Conversation.buyer_user_id == current_user.id) | (Conversation.seller_user_id == current_user.id)).order_by(Conversation.last_message_at.desc()).all()
    return render_template('chat/index.html', conversations=conversations, active_conv=None)

@chat_bp.route('/<int:conv_id>')
@login_required
def view_chat(conv_id):
    conversations = Conversation.query.filter((Conversation.buyer_user_id == current_user.id) | (Conversation.seller_user_id == current_user.id)).order_by(Conversation.last_message_at.desc()).all()
    active_conv = Conversation.query.get_or_404(conv_id)
    if active_conv.buyer_user_id != current_user.id and active_conv.seller_user_id != current_user.id:
        return redirect(url_for('chat.index'))
    return render_template('chat/index.html', conversations=conversations, active_conv=active_conv)

@chat_bp.route('/start/<int:listing_id>')
@login_required
def start_chat(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.user_id == current_user.id: return redirect(url_for('listings.details', listing_id=listing_id))
    conv = Conversation.query.filter_by(listing_id=listing_id, buyer_user_id=current_user.id, seller_user_id=listing.user_id).first()
    if not conv:
        conv = Conversation(listing_id=listing_id, buyer_user_id=current_user.id, seller_user_id=listing.user_id)
        db.session.add(conv)
        db.session.commit()
    return redirect(url_for('chat.view_chat', conv_id=conv.id))

@socketio.on('join')
def on_join(data):
    join_room(str(data['room']))

@socketio.on('send_message')
def handle_message(data):
    room = str(data['room'])
    msg = Message(conversation_id=room, sender_user_id=int(data['sender_id']), message_text=data['message'])
    db.session.add(msg)
    Conversation.query.get(room).last_message_at = datetime.utcnow()
    db.session.commit()
    emit('receive_message', {'text': data['message'], 'sender_id': int(data['sender_id']), 'created_at': msg.created_at.strftime('%H:%M')}, room=room)
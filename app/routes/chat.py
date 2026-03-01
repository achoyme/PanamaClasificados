from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.chat import Conversation, Message
from app.models import Listing
from datetime import datetime

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/')
@login_required
def index():
    conversations = Conversation.query.filter(
        (Conversation.buyer_user_id == current_user.id) | 
        (Conversation.seller_user_id == current_user.id)
    ).order_by(Conversation.last_message_at.desc()).all()
    return render_template('chat/index.html', conversations=conversations, active_conv=None)

@chat_bp.route('/<int:conv_id>')
@login_required
def view_chat(conv_id):
    conversations = Conversation.query.filter(
        (Conversation.buyer_user_id == current_user.id) | 
        (Conversation.seller_user_id == current_user.id)
    ).order_by(Conversation.last_message_at.desc()).all()
    
    active_conv = Conversation.query.get_or_404(conv_id)
    
    if active_conv.buyer_user_id != current_user.id and active_conv.seller_user_id != current_user.id:
        return redirect(url_for('chat.index'))
        
    # ✅ CORRECCIÓN: Marcar mensajes como leídos al abrir el chat
    unread_msgs = Message.query.filter_by(conversation_id=active_conv.id, is_read=False).filter(Message.sender_user_id != current_user.id).all()
    if unread_msgs:
        for msg in unread_msgs:
            msg.is_read = True
        db.session.commit()
    
    return render_template('chat/index.html', conversations=conversations, active_conv=active_conv)

@chat_bp.route('/start/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def start_chat(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    if listing.user_id == current_user.id: 
        return redirect(url_for('listings.details', listing_id=listing_id))
    
    conv = Conversation.query.filter_by(
        listing_id=listing_id, 
        buyer_user_id=current_user.id, 
        seller_user_id=listing.user_id
    ).first()
    
    if not conv:
        conv = Conversation(
            listing_id=listing_id, 
            buyer_user_id=current_user.id, 
            seller_user_id=listing.user_id
        )
        db.session.add(conv)
        db.session.commit()
        
    message_text = request.form.get('message')
    if message_text and message_text.strip():
        msg = Message(
            conversation_id=conv.id,
            sender_user_id=current_user.id,
            message_text=message_text.strip()
        )
        db.session.add(msg)
        conv.last_message_at = datetime.utcnow()
        db.session.commit()
        flash('¡Mensaje enviado! Ahora estás en un chat privado con el vendedor.', 'success')
    
    return redirect(url_for('chat.view_chat', conv_id=conv.id))

@chat_bp.route('/start_with_user/<int:listing_id>/<int:buyer_id>')
@login_required
def start_chat_with_user(listing_id, buyer_id):
    listing = Listing.query.get_or_404(listing_id)
    
    if listing.user_id != current_user.id:
        flash('No autorizado', 'error')
        return redirect(url_for('listings.details', listing_id=listing_id))
        
    conv = Conversation.query.filter_by(
        listing_id=listing_id, 
        buyer_user_id=buyer_id, 
        seller_user_id=current_user.id
    ).first()
    
    if not conv:
        conv = Conversation(
            listing_id=listing_id, 
            buyer_user_id=buyer_id, 
            seller_user_id=current_user.id
        )
        db.session.add(conv)
        db.session.commit()
        
        question_text = request.args.get('q_text')
        if question_text:
            msg = Message(
                conversation_id=conv.id,
                sender_user_id=buyer_id,
                message_text=f"Consulta pública realizada: {question_text}"
            )
            db.session.add(msg)
            db.session.commit()

    flash('Chat privado iniciado. Puedes responder a su consulta aquí.', 'success')
    return redirect(url_for('chat.view_chat', conv_id=conv.id))

@chat_bp.route('/<int:conv_id>/send', methods=['POST'])
@login_required
def send_message(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    
    if conv.buyer_user_id != current_user.id and conv.seller_user_id != current_user.id:
        return redirect(url_for('chat.index'))
    
    message_text = request.form.get('message', '').strip()
    if message_text:
        msg = Message(
            conversation_id=conv_id,
            sender_user_id=current_user.id,
            message_text=message_text
        )
        db.session.add(msg)
        conv.last_message_at = datetime.utcnow()
        db.session.commit()
    
    return redirect(url_for('chat.view_chat', conv_id=conv_id))
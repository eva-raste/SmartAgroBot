# your_app/views.py

from django.shortcuts import render, redirect
from chatbot.utils import handle_user_input, speak_text 
from django.views.decorators.http import require_POST
from django.utils.html import linebreaks
import markdown

def markdown_to_html(text):
    return markdown.markdown(text)

def chatbot_view(request):
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []

    if request.method == 'POST':
        user_input = request.POST.get('user_input', '').strip()
        input_mode = request.POST.get('input_mode', 'text')  # Default is 'text'

        if user_input:
            bot_response = handle_user_input(user_input)
            formatted_response = linebreaks(bot_response)
            bot_response_html = markdown_to_html(bot_response)

            # ✅ Only speak if input came from voice
            if input_mode == 'voice':
                speak_text(bot_response)

            request.session['chat_history'].append({
                'user': user_input,
                'bot': formatted_response
            })
            request.session.modified = True

        return redirect('chatbot')

    return render(request, 'chatbot/chat.html', {
        'chat_history': request.session['chat_history']
    })

@require_POST
def clear_chat(request):
    print("--- Clearing chat history ---") # Debug print
    request.session['chat_history'] = []
    request.session.modified = True # Ensure session is marked as modified after clearing
    return redirect('chatbot')
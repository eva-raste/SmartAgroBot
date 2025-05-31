# your_app/views.py

from django.shortcuts import render, redirect
from chatbot.utils import handle_user_input 
from django.views.decorators.http import require_POST
from django.utils.html import linebreaks

def chatbot_view(request):
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []

    if request.method == 'POST':
        user_input = request.POST.get('user_input', '').strip()

        if user_input: 
            bot_response = handle_user_input(user_input)

            formatted_response = linebreaks(bot_response)

            request.session['chat_history'].append({
                'user': user_input,
                'bot': formatted_response
            })
            request.session.modified = True

        return redirect('chatbot')  

    # For GET requests
    return render(request, 'chatbot/chat.html', {
        'chat_history': request.session['chat_history']
    })


@require_POST
def clear_chat(request):
    print("--- Clearing chat history ---") # Debug print
    request.session['chat_history'] = []
    request.session.modified = True # Ensure session is marked as modified after clearing
    return redirect('chatbot')
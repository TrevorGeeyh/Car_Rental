document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const quickQuestions = document.querySelectorAll('.quick-question');
    const typingIndicator = document.querySelector('.ai-typing-indicator');
    
    // 自动滚动到聊天区域底部
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 页面加载时滚动到底部
    scrollToBottom();
    
    // 快速问题点击事件
    quickQuestions.forEach(button => {
        button.addEventListener('click', function() {
            messageInput.value = this.textContent;
            messageInput.focus();
        });
    });
    
    // 表单提交处理
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (message === '') return;
        
        // 添加用户消息到聊天区域
        const currentTime = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const userMessageHtml = `
            <div class="d-flex justify-content-end mb-3">
                <div class="message message-user">
                    <p class="mb-0">${message}</p>
                    <div class="message-time">${currentTime}</div>
                </div>
                <div class="avatar avatar-user ms-2">
                    <i class="fas fa-user"></i>
                </div>
            </div>
        `;
        
        chatMessages.insertAdjacentHTML('beforeend', userMessageHtml);
        scrollToBottom();
        
        // 显示AI正在输入的指示器
        typingIndicator.style.display = 'flex';
        scrollToBottom();
        
        // 清空输入框
        messageInput.value = '';
        
        // 获取CSRF Token
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        // 获取会话ID
        const session_id = document.getElementById('chat-session-id').value || localStorage.getItem('chat_session_id') || '';
        
        // 发送AJAX请求到后端
        fetch('/ai-customer-service/send-message/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                'message': message,
                'session_id': session_id
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应异常');
            }
            return response.json();
        })
        .then(data => {
            // 隐藏输入指示器
            typingIndicator.style.display = 'none';
            
            // 如果有会话ID，保存到本地存储
            if (data.session_id) {
                localStorage.setItem('chat_session_id', data.session_id);
            }
            
            // 添加AI回复到聊天区域
            let aiMessageContent = '';
            
            if (data.status === 'error') {
                // 处理错误消息
                aiMessageContent = `<p class="mb-0">${data.content || '抱歉，服务器遇到了问题。请稍后再试。'}</p>`;
            }
            else if (data.type === 'text') {
                // 处理文本消息
                aiMessageContent = `<p class="mb-0">${data.content.replace(/\n/g, '<br>')}</p>`;
            } 
            else if (data.type === 'car_recommendation') {
                // 添加AI回复文本
                aiMessageContent = `<p class="mb-0">${data.content.replace(/\n/g, '<br>')}</p>`;
                
                // 添加车辆推荐卡片
                if (data.cars && data.cars.length > 0) {
                    aiMessageContent += `<div class="recommendation-cards mt-3">`;
                    
                    // 循环添加每辆推荐车型的卡片
                    data.cars.forEach(car => {
                        // 确保所有必要的属性都存在
                        const brand = car.brand || '未知品牌';
                        const model = car.model || '未知型号';
                        const category = car.category || '未分类';
                        const daily_rate = car.daily_rate || 0;
                        const seats = car.seats || '未知';
                        const transmission = car.transmission || '未知';
                        const location = car.location_name ? `<p class="card-text mb-1"><small class="text-muted"><i class="fas fa-map-marker-alt me-1"></i>${car.location_name}</small></p>` : '';
                        
                        aiMessageContent += `
                            <div class="recommendation-card mb-2">
                                <div class="row g-0">
                                    <div class="col-4">
                                        <div class="text-center">
                                            ${car.image_url ? 
                                              `<img src="${car.image_url}" class="img-fluid rounded" alt="${brand} ${model}">` : 
                                              `<div class="bg-light d-flex align-items-center justify-content-center rounded" style="height: 80px;">
                                                  <i class="fas fa-car text-secondary" style="font-size: 2rem;"></i>
                                               </div>`
                                            }
                                        </div>
                                    </div>
                                    <div class="col-8">
                                        <div class="card-body p-2">
                                            <h6 class="card-title mb-1">${brand} ${model}</h6>
                                            <p class="card-text mb-1"><small class="text-muted">¥${daily_rate}/天 | ${category}</small></p>
                                            ${location}
                                            <p class="card-text mb-1"><small><i class="fas fa-users me-1"></i>${seats}座 | <i class="fas fa-cog me-1"></i>${transmission}</small></p>
                                            <a href="/cars/${car.id}/" class="btn btn-sm btn-outline-primary mt-1">查看详情</a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    aiMessageContent += `</div>`;
                } else {
                    // 没有车辆可推荐
                    aiMessageContent += `<div class="alert alert-info mt-2">
                        <i class="fas fa-info-circle me-2"></i>很抱歉，没有找到符合条件的车辆。
                    </div>`;
                }
            }
            
            const aiMessageHtml = `
                <div class="d-flex mb-3">
                    <div class="avatar avatar-ai">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message message-ai">
                        ${aiMessageContent}
                        <div class="message-time">${data.timestamp ? new Date(data.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : currentTime}</div>
                    </div>
                </div>
            `;
            
            chatMessages.insertAdjacentHTML('beforeend', aiMessageHtml);
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
            
            // 添加错误消息
            const errorMessageHtml = `
                <div class="d-flex mb-3">
                    <div class="avatar avatar-ai">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message message-ai">
                        <p class="mb-0">抱歉，我遇到了一些问题。请稍后再试或联系客服。</p>
                        <div class="message-time">${currentTime}</div>
                    </div>
                </div>
            `;
            
            chatMessages.insertAdjacentHTML('beforeend', errorMessageHtml);
            scrollToBottom();
        });
    });
    
    // 语音输入功能
    const voiceButton = document.querySelector('.form-voice');
    
    if ('webkitSpeechRecognition' in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'zh-CN';
        
        let isRecording = false;
        
        voiceButton.addEventListener('click', function() {
            if (isRecording) {
                recognition.stop();
                voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
                voiceButton.classList.remove('btn-danger');
                voiceButton.classList.add('btn-outline-secondary');
            } else {
                recognition.start();
                voiceButton.innerHTML = '<i class="fas fa-stop"></i>';
                voiceButton.classList.remove('btn-outline-secondary');
                voiceButton.classList.add('btn-danger');
            }
            
            isRecording = !isRecording;
        });
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            messageInput.value = transcript;
            voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
            voiceButton.classList.remove('btn-danger');
            voiceButton.classList.add('btn-outline-secondary');
            isRecording = false;
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error', event.error);
            voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
            voiceButton.classList.remove('btn-danger');
            voiceButton.classList.add('btn-outline-secondary');
            isRecording = false;
        };
    } else {
        voiceButton.style.display = 'none';
    }
}); 
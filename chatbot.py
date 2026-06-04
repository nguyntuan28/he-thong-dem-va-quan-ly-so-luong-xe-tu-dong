"""
chatbot.py - AI Chatbot for Smart Traffic City
Hệ thống trò chuyện AI hỗ trợ thành phố giao thông thông minh
"""

import os
from datetime import datetime
from typing import Optional, List, Dict


class TrafficCityBot:
    """
    AI Chatbot cho hệ thống giao thông thông minh.
    
    Features:
    - Phân tích thống kê giao thông
    - Cảnh báo vi phạm
    - Gợi ý tối ưu hóa
    - Q&A về hệ thống
    - Thông tin thành phố thông minh
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Khởi tạo chatbot.
        
        Args:
            api_key: OpenAI API key. Nếu không có, sẽ dùng chế độ demo.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.using_openai = self.api_key is not None
        self.conversation_history: List[Dict] = []
        
        # Hệ thống prompt cho AI
        self.system_prompt = """Bạn là một trợ lý AI thông minh cho hệ thống giao thông thành phố.
        
Chuyên môn:
- Phân tích dữ liệu giao thông (lưu lượng xe, vi phạm, tắc đường)
- Gợi ý cách tối ưu hóa giao thông
- Giải thích các vi phạm giao thông
- Trả lời câu hỏi về hệ thống giám sát
- Cung cấp thông tin về thành phố thông minh

Hành động:
1. Khi người dùng hỏi về thống kê, hãy phân tích dữ liệu được cung cấp
2. Gợi ý giải pháp thực tế để giảm tắc đường
3. Giải thích các vi phạm một cách chi tiết
4. Dùng tiếng Việt, rõ ràng và dễ hiểu
5. Tương tác thân thiện, chuyên nghiệp

Format: Hãy trả lời ngắn gọn (1-2 đoạn), sử dụng emoji để dễ đọc."""

        # Khởi tạo OpenAI nếu có API key
        if self.using_openai:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("⚠️ Cần cài đặt: pip install openai")
                self.using_openai = False

    def chat(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        Trò chuyện với AI.
        
        Args:
            user_message: Tin nhắn từ người dùng
            context: Ngữ cảnh (thống kê, dữ liệu job, v.v.)
            
        Returns:
            Phản hồi từ AI
        """
        # Thêm ngữ cảnh nếu có
        if context:
            context_text = self._format_context(context)
            full_message = f"{context_text}\n\nCâu hỏi: {user_message}"
        else:
            full_message = user_message
        
        # Lưu vào lịch sử
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Lấy phản hồi
        if self.using_openai:
            response = self._chat_with_openai(full_message)
        else:
            response = self._chat_demo_mode(user_message, context)
        
        # Lưu phản hồi
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response

    def _chat_with_openai(self, message: str) -> str:
        """Gọi OpenAI API."""
        try:
            # Chuẩn bị messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Thêm lịch sử (giới hạn 10 tin nhắn gần nhất)
            for msg in self.conversation_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Gọi API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Lỗi kết nối OpenAI: {str(e)}"

    def _chat_demo_mode(self, message: str, context: Optional[Dict] = None) -> str:
        """Chế độ demo (không cần API key)."""
        message_lower = message.lower()
        
        # Phân tích thống kê
        if 'thống kê' in message_lower or 'xe' in message_lower:
            if context and 'total_vehicles' in context:
                total = context.get('total_vehicles', 0)
                violations = context.get('total_violations', 0)
                return f"""📊 **Phân tích Giao Thông**

Tổng xe phát hiện: **{total}** chiếc
Vi phạm ghi nhận: **{violations}** lần
Tỷ lệ vi phạm: **{(violations/max(total, 1)*100):.1f}%**

💡 Đề xuất: Tăng cường giám sát tại các điểm nóng vi phạm để giảm tỷ lệ này."""
            else:
                return """📊 **Phân tích Giao Thông**

Hệ thống đang theo dõi lưu lượng giao thông theo thời gian thực.
Tải một video lên để bắt đầu phân tích! 🚀"""
        
        # Gợi ý tối ưu hóa
        elif 'tối ưu' in message_lower or 'gợi ý' in message_lower:
            return """🔧 **Gợi ý Tối ưu Giao Thông**

1. **Thời gian tín hiệu**: Điều chỉnh tín hiệu đèn dự trên lưu lượng thực tế
2. **Phân tán lưu lượng**: Hướng dẫn xe qua các tuyến phụ ít tắc
3. **Xử phạt vi phạm**: Tăng cường phạt để giảm vi phạm
4. **Quản lý bãi đỗ**: Cung cấp thông tin chỗ đỗ để giảm tìm kiếm

📱 Ứng dụng di động sẽ giúp người dùng hơn!"""
        
        # Thông tin hệ thống
        elif 'hệ thống' in message_lower or 'làm cách nào' in message_lower:
            return """ℹ️ **Hệ thống Giám sát Giao thông**

**Tính năng:**
- 🎥 Xử lý video thời gian thực với AI (YOLOv8)
- 📍 Phát hiện vi phạm vượt đèn đỏ
- 📊 Thống kê chi tiết lưu lượng xe
- 💾 Lưu trữ lịch sử xử lý

**Cách dùng:**
1. Tải video lên tab Upload
2. Chọn tham số (confidence, IoU)
3. Nhấn "UPLOAD & XỬ LÝ"
4. Xem kết quả trong tab History

📚 Xem thêm: History, Results, Settings"""
        
        # Mặc định
        else:
            return f"""👋 **Trợ lý Giao thông Thông minh**

Tôi có thể giúp bạn:
- 📊 Phân tích dữ liệu giao thông
- 🔧 Gợi ý tối ưu hóa
- ⚠️ Giải thích vi phạm
- ❓ Trả lời câu hỏi về hệ thống

Bạn muốn biết gì? Hãy hỏi tôi! 😊"""

    def _format_context(self, context: Dict) -> str:
        """Định dạng ngữ cảnh thành text."""
        lines = ["📋 **Ngữ cảnh hiện tại:**"]
        
        if 'total_vehicles' in context:
            lines.append(f"- Tổng xe: {context['total_vehicles']}")
        if 'total_violations' in context:
            lines.append(f"- Vi phạm: {context['total_violations']}")
        if 'job_count' in context:
            lines.append(f"- Jobs xử lý: {context['job_count']}")
        if 'traffic_density' in context:
            lines.append(f"- Mật độ giao thông: {context['traffic_density']}")
        
        return "\n".join(lines)

    def clear_history(self):
        """Xóa lịch sử trò chuyện."""
        self.conversation_history = []

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Lấy lịch sử trò chuyện."""
        return self.conversation_history[-limit:]

    def get_status(self) -> Dict:
        """Lấy trạng thái chatbot."""
        return {
            'using_openai': self.using_openai,
            'api_key_configured': self.api_key is not None,
            'conversation_count': len(self.conversation_history),
            'status': '🟢 OpenAI Active' if self.using_openai else '🟡 Demo Mode (không cần API key)'
        }


# ──────────────────────────────────────────────────────────
# Initialize global chatbot instance
# ──────────────────────────────────────────────────────────
try:
    traffic_bot = TrafficCityBot()
except Exception as e:
    print(f"⚠️ Lỗi khởi tạo chatbot: {e}")
    traffic_bot = None

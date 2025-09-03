import json
import os
import threading
import time
from datetime import datetime
import google.generativeai as genai

class SimpleRAG:
    def __init__(self):
        self.knowledge_base = []
        self.manual_data = []
        self.gemini_model = None
        self.load_data()
        self.setup_gemini()
        self.start_auto_refresh()
    
    def setup_gemini(self):
        """Setup Google Gemini LLM"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("⚠️ GEMINI_API_KEY not found in environment")
                self.gemini_model = None
                return
                
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            print("🤖 Gemini LLM loaded successfully!")
        except Exception as e:
            print(f"⚠️ Gemini not available: {e}")
            self.gemini_model = None
    
    def load_data(self):
        try:
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
        except FileNotFoundError:
            self.knowledge_base = []
        
        try:
            with open('manual_data.json', 'r', encoding='utf-8') as f:
                self.manual_data = json.load(f)
        except FileNotFoundError:
            self.manual_data = []
    
    def start_auto_refresh(self):
        """Auto-refresh every 2 hours"""
        def refresh_loop():
            while True:
                time.sleep(7200)  # 2 hours
                try:
                    from scraper import DAVScraper
                    scraper = DAVScraper()
                    scraper.scrape_all()
                    self.load_data()
                    print(f"🔄 Auto-refreshed at {datetime.now()}")
                except Exception as e:
                    print(f"Auto-refresh error: {e}")
        
        thread = threading.Thread(target=refresh_loop, daemon=True)
        thread.start()
    
    def search(self, query, top_k=3):
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 2]
        
        all_data = self.knowledge_base + self.manual_data
        results = []
        
        for item in all_data:
            content_lower = item['content'].lower()
            title_lower = item.get('title', '').lower()
            
            score = 0
            
            if query_lower in content_lower or query_lower in title_lower:
                score += 15
            
            for word in query_words:
                if word in content_lower:
                    score += 3
                if word in title_lower:
                    score += 5
            
            category = item.get('category', 'general').lower()
            if any(word in category for word in query_words):
                score += 2
            
            if score > 0:
                results.append((item, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in results[:top_k]]
    
    def call_gemini(self, prompt):
        """Call Google Gemini LLM"""
        if not self.gemini_model:
            return None
        
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip() if response.text else None
        except Exception as e:
            print(f"Gemini error: {e}")
            return None
    
    def make_links_clickable(self, text):
        """Convert URLs to clickable links"""
        import re
        url_pattern = r'(https?://[^\s]+)'
        return re.sub(url_pattern, r'<a href="\1" target="_blank" style="color: #004aad; text-decoration: underline;">\1</a>', text)
    
    def check_holiday_query(self, query):
        """Check if query is asking about holidays"""
        holiday_keywords = ['holiday', 'holidays', 'festival', 'celebration', 'off', 'leave', 'vacation']
        month_keywords = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 
            'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        query_lower = query.lower()
        
        # Check if asking about holidays
        if any(keyword in query_lower for keyword in holiday_keywords):
            # Extract month if mentioned
            month = None
            for month_name, month_num in month_keywords.items():
                if month_name in query_lower:
                    month = month_num
                    break
            
            return True, month
        
        return False, None
    
    def fetch_holidays_from_db(self, month=None, year=None):
        """Fetch holidays from database"""
        try:
            import requests
            from datetime import datetime
            
            if not year:
                year = datetime.now().year
            
            response = requests.post('http://localhost:5000/get_holidays', 
                                   json={'month': month, 'year': year}, 
                                   timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    return data['holidays']
            
        except Exception as e:
            print(f"Error fetching holidays: {e}")
        
        return []
    def generate_response(self, query):
        # Check if asking about holidays
        is_holiday_query, month = self.check_holiday_query(query)
        
        if is_holiday_query:
            holidays = self.fetch_holidays_from_db(month)
            
            if holidays:
                if month:
                    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                                 'July', 'August', 'September', 'October', 'November', 'December']
                    month_name = month_names[month] if month <= 12 else 'the specified month'
                    response = f"**Holidays in {month_name}:**\n\n"
                else:
                    response = "**Upcoming Holidays:**\n\n"
                
                for holiday in holidays:
                    response += f"🎉 **{holiday['title']}** - {holiday['date']}\n"
                    if holiday['description']:
                        response += f"   {holiday['description']}\n"
                    response += "\n"
                
                return response
            else:
                if month:
                    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                                 'July', 'August', 'September', 'October', 'November', 'December']
                    month_name = month_names[month] if month <= 12 else 'that month'
                    return f"No holidays found for {month_name}. Please check back later for updates on school events and holidays."
                else:
                    return "No holidays found in our calendar. Please check back later for updates on school events and holidays."
        
        # Continue with regular RAG processing
        # Always search for school-related content first
        results = self.search(query)
        
        # Check if query is school-related or ambiguous (could relate to school)
        school_keywords = ['dav', 'school', 'admission', 'fee', 'timing', 'event', 'contact', 'facility', 'teacher', 'student', 'class', 'koyla', 'nagar']
        ambiguous_keywords = ['address', 'location', 'phone', 'number', 'timing', 'time', 'fee', 'cost', 'contact', 'where', 'when', 'how much', 'principal', 'staff', 'facilities', 'events', 'activities']
        
        is_school_related = any(keyword in query.lower() for keyword in school_keywords)
        is_ambiguous = any(keyword in query.lower() for keyword in ambiguous_keywords)
        
        if results and (is_school_related or is_ambiguous):
            # School-related or ambiguous query - prioritize school information
            best_result = results[0]
            content = best_result['content']
            url = best_result.get('url', '')
            
            gemini_prompt = f"""You are DAVGPT, an AI assistant for DAV Koyla Nagar school. The user asked: "{query}"

If the question is ambiguous (like "address", "timing", "fees", etc.), assume they're asking about DAV Koyla Nagar school specifically.

School Information: {content[:800]}

Provide a helpful answer focusing on DAV Koyla Nagar school:"""
            
            gemini_response = self.call_gemini(gemini_prompt)
            
            if gemini_response and len(gemini_response) > 20:
                response = gemini_response
            else:
                # Fallback with school context
                query_lower = query.lower()
                if any(word in query_lower for word in ['address', 'location', 'where']):
                    response = f"**DAV Koyla Nagar School Address:**\n\n{content[:400]}"
                elif any(word in query_lower for word in ['phone', 'contact', 'number']):
                    response = f"**DAV Koyla Nagar Contact Information:**\n\n{content[:400]}"
                elif any(word in query_lower for word in ['timing', 'time', 'hours']):
                    response = f"**DAV Koyla Nagar School Timings:**\n\n{content[:400]}"
                elif any(word in query_lower for word in ['fee', 'cost', 'payment']):
                    response = f"**DAV Koyla Nagar Fee Structure:**\n\n{content[:400]}"
                else:
                    response = f"**About DAV Koyla Nagar School:**\n\n{content[:400]}"
            
            # Make links clickable and add source
            response = self.make_links_clickable(response)
            if url and url != 'manual_entry':
                response += f'\n\n🔗 **More details:** <a href="{url}" target="_blank" style="color: #004aad; text-decoration: underline;">{url}</a>'
            
            return response
        
        # General query - still mention school context when possible
        gemini_prompt = f"""You are DAVGPT, an AI assistant for DAV Koyla Nagar school. Answer the user's question naturally. When appropriate, you can relate the answer to education or school context.

User Question: {query}

Provide a helpful answer (mention DAV Koyla Nagar school context if relevant):"""
        
        gemini_response = self.call_gemini(gemini_prompt)
        
        if gemini_response and len(gemini_response) > 20:
            return gemini_response
        
        # Fallback response
        return f"""I can help you with that! As DAVGPT for DAV Koyla Nagar school, I can discuss various topics.

For school-specific information, I have details about:
🏫 **Address & Location** • 📞 **Contact Numbers** • ⏰ **School Timings** 
🎓 **Admissions** • 💰 **Fees** • 🎉 **Events** • 🏗️ **Facilities**

Feel free to ask me anything - I'll prioritize DAV Koyla Nagar school information when relevant!"""
    
    def add_manual_entry(self, entry):
        self.manual_data.append(entry)
        self.save_manual_data()
    
    def save_manual_data(self):
        with open('manual_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.manual_data, f, indent=2, ensure_ascii=False)
    
    def refresh_knowledge_base(self):
        self.load_data()
        return True

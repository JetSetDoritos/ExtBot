from extbot.messages_collector import MessagesCollector

#recreates (or initially creates) the database

m_c = MessagesCollector()

m_c.get_messages()
m_c.update_names()
m_c.get_likes()
m_c.get_kicks()
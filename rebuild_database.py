from extbot.messages_collector import MessagesCollector
import os
#recreates (or initially creates) the database

m_c = MessagesCollector()

curr_db = os.path.join('data','exdatabase.sqlite3')
try:
  os.remove(curr_db)
except:
  pass

print("Working with Group:")
print(m_c.get_group_info_message())
print("This may take some time!")
total = m_c.get_total_messages()
print("Your group has %s messages, this may take at least %s minutes." % (total, total/6000))
print("Requesting messages...")
m_c.get_messages()
m_c.update_names()
m_c.get_likes()
m_c.get_kicks()

print("Complete!")

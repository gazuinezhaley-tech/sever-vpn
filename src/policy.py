import time
def allowed(user,now=None):
 now=time.time() if now is None else now
 return bool(user.get('enabled',False)) and (not user.get('expires_at') or user['expires_at']>now) and (not user.get('quota_bytes') or user.get('used_bytes',0)<user['quota_bytes'])

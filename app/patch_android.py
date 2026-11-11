# Permisos que usa la guía: internet y ubicación (para "Cerca de mí" y sellar el pasaporte).
p="android/app/src/main/AndroidManifest.xml"; s=open(p).read()
add='''    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-feature android:name="android.hardware.location.gps" android:required="false" />
'''
if "ACCESS_FINE_LOCATION" not in s: s=s.replace("</manifest>", add+"</manifest>")
open(p,"w").write(s); print("manifest ok")

# Textos de permisos y ajustes para la App Store.
import plistlib
p="ios/App/App/Info.plist"; d=plistlib.load(open(p,"rb"))
d["NSLocationWhenInUseUsageDescription"]="La guía usa tu ubicación para mostrarte los lugares cercanos y sellar el pasaporte. No sale de tu teléfono."
d["ITSAppUsesNonExemptEncryption"]=False
d["CFBundleDisplayName"]="Ribera Baja"
d["UIRequiresFullScreen"]=False
plistlib.dump(d,open(p,"wb")); print("Info.plist ok")

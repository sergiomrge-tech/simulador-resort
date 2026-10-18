import sys
from PIL import Image
names="entrada recepcao piscina bangalo interior bar praia noite".split()
ims=[Image.open(f'shots/{n}.png').convert('RGB').resize((640,360)) for n in names]
S=Image.new('RGB',(1280,1440))
for i,im in enumerate(ims): S.paste(im,((i%2)*640,(i//2)*360))
S.save(sys.argv[1] if len(sys.argv)>1 else 'shots/sheet.png')

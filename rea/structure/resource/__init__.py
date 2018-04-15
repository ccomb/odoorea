from . import model, conversion  # noqa
from os.path import join, dirname

entity = model.__name__.split('.')[-2]
# dynamically generated view for behaviours
for behaviour in ('lifecycle',
                  'identifier',
                  'property'):
    source = join(dirname(dirname(dirname(model.__file__))),
                  'behaviour', behaviour, behaviour + '.tmpl.xml')
    target = join(dirname(model.__file__), behaviour + '.xml')
    content = (open(source).read()
               .replace('${object}', entity)
               .replace('${Object}', entity.capitalize()))
    open(target, 'w').write(content)

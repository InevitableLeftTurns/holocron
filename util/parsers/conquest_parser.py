import json

data = {}

with open('data/conquest/import.txt') as importfile:
    line = importfile.readline()
    header = None
    header_id = None
    boss_counter = 1
    feat_counter = 0
    while line:
        line = line.strip("\n")
        if line.startswith('@@'):
            # begin new section
            feat_counter = 0
            line = line.strip('@@')
            header = line
            header_id = None

            # sector header with sector number
            if ' ' in line:
                header, header_id = line.split(' ')
            print(f'{header}:{header_id}')
        elif line and line != '----':
            if ':' in line:
                boss_type, description = line.split(':', 1)
            else:
                boss_type = None
                description = line
                feat_counter += 1

            # location code
            location = header.lower()[0]
            if header_id:
                location += header_id

            if boss_type:
                # handle boss location m or b
                location += boss_type.lower()[0]
                boss_counter = (boss_counter + 1) % 2
                location += str(boss_counter + 1)
            elif header_id:
                # sectors
                location += f'f{feat_counter}'
            else:
                # globals have no f
                location += str(feat_counter)

            print(f'{location}: {description.strip()}')
            data[location] = description.strip()

        line = importfile.readline()

with open('data/conquest/labels.json', 'w') as jsonfile:
    json.dump(data, jsonfile)
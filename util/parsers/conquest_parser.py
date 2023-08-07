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
            if ' ' in line:
                header, header_id = line.split(' ')
            print(f'{header}:{header_id}')

        if ':' in line:
            description = line.split(':', 1)
            if len(description) > 0 and description[0] \
                    and not description[0].startswith('-') \
                    and not description[0].endswith('Bosses'):
                desc_text = description[0]
                boss_type = None
                # bosses have a ' - '
                if ' - ' in desc_text:
                    boss_type_data, desc_text = desc_text.split(' - ')
                    boss_type = boss_type_data.split(' ')[-1]
                    print(f"boss: {boss_type}")
                else:
                    feat_counter += 1

                location = header.lower()[0]
                if header_id:
                    location += header_id
                if boss_type:
                    location += boss_type.lower()[0]
                    boss_counter = (boss_counter + 1) % 2
                    location += str(boss_counter + 1)
                elif header_id:
                    location += f'f{feat_counter}'
                else:
                    location += str(feat_counter)

                print(f'{location}: {desc_text}')
                data[location] = desc_text

        line = importfile.readline()

with open('data/conquest/labels.json', 'w') as jsonfile:
    json.dump(data, jsonfile)
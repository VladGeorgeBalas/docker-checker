'''
Autor: Balas Vlad-George

Idee de functionare:
    - se citeste un .csv cu detaliile studentilor si repo-urile lor
    - pt fiecare student:
        - se descarca repo-ul si o copie proaspata a checker-ului
        - se da bind intre container-ul de docker si fisierele de pe calculator
        - se executa comenzile:
            - descarca dependente
            - ofera drepturi de executue
            - executa checker
        - se sterg fisierele locale
        - se adauga rezultatul la output
    - se inchide fisierul de output
'''

import docker
from git import Repo
import shutil
import os
import json

config_json = open("config.json", "r").read()
config_dict = json.loads(config_json)

#citim lista studenti si detaliile lor
det_stud = []
file_stud = open(config_dict["in"], 'r').readlines()
for i in file_stud:
    det_stud.append(i.replace('\n', '').split(","))
print(det_stud)

git_chk = config_dict["checker"]

#fisierul de iesire
file_out = open(config_dict["out"], "w")

for stud in det_stud:
    git_src = stud[config_dict["in_fields"].index("git")]
    
    #downloadeaza codul studentului
    dir_src = "/tmp/src/"
    Repo.clone_from(git_src, dir_src)
    print(dir_src)

    #downloadeaza checker-ul
    dir_chk = "/tmp/chk"
    Repo.clone_from(git_chk, dir_chk)
    print(dir_chk)

    # rulam docker-ul
    client = docker.from_env()

    # legam docker cu host
    mnt_src = docker.types.Mount(target = '/tmp/src', source = dir_src, type='bind')
    mnt_chk = docker.types.Mount(target = '/tmp/chk', source = dir_chk, type='bind')

    cmd = [
            "sudo apt-get install make gcc>/dev/null 2>&1", #instalare pachete necesare
            "chmod +x chk/checker.sh", #setare env
            "./chk/checker.sh src" #rulare checker pentru folder-ul src
            ]
    cmd_cat = ""
    for i in cmd:
        cmd_cat += i + ";"

    # rulam checker-ul pe docker
    # comanda este folosita pentru a inlatui mai multe comenzi, altfel le combina si de eroare( ex "./a & ./b" == "./a ./b" => eroare)
    # trebuie ori facuta imagine custom ori instalate utilitarele pre check
    # !! in caz de foarte multe comenzi se poate aduaga un setup.sh in acelasi git cu checker.sh !!
    res = client.containers.run(image = 'debian',auto_remove = True, mounts = [mnt_src, mnt_chk], working_dir = '/tmp', command = "/bin/bash -c '" + cmd_cat + "'", user='root')
    print(res)
    
    #linia cu iesirea
    out = ""
    for i in config_dict["out_fields"]:
        if i != "res":
            out += stud[config_dict["in_fields"].index(i)] + ","
        else:
            for i in res.decode('utf-8').replace('\n', '').split(' '):
                out = out + i + ','

    file_out.write(out + '\n')

    shutil.rmtree(dir_chk)
    shutil.rmtree(dir_src)

file_out.close()

#pachete necesare docker ( cu grup de utilizatori docker ), shutil, GitPython
#script scris si testat DOAR pe linux-debian-12

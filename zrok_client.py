import os
import subprocess
import sys
import tarfile
import time
import urllib.request
import re
from collections import defaultdict
import shutil
import zipfile
import json
import ssl
import winreg
import nbtlib

ssl._create_default_https_context = ssl._create_unverified_context

temp_tar_path = os.path.join(os.getenv("TEMP"), "zrok.tar.gz")
minecraft_path = os.path.join(os.getenv("APPDATA"), ".minecraft", "zrok")
zrok_exe_path = os.path.join(minecraft_path, "zrok.exe")


def get_latest_version_info(url):
    api_url = "https://api.github.com/repos/openziti/zrok/releases/latest"
    with urllib.request.urlopen(url) as response:
        release_data = json.loads(response.read())
        tag_name = release_data["tag_name"]
        version = tag_name.lstrip("v")
        return version, tag_name


def download_mods():
    def process_mods_folder(mods_folder):
        files = [f for f in os.listdir(mods_folder) if os.path.isfile(os.path.join(mods_folder, f))]
        pattern = re.compile(r'^(.*?)(?:\((\d+)\))?(\.[^.]*)$')
        file_groups = defaultdict(list)
        for file in files:
            match = pattern.fullmatch(file)
            if match:
                base = match.group(1).rstrip('-')
                num = match.group(2)
                ext = match.group(3)
                key = (base, ext)
                file_groups[key].append({
                    'num': int(num) if num else 0,
                    'name': file,
                    'path': os.path.join(mods_folder, file)
                })

        processed = 0
        for (base, ext), versions in file_groups.items():
            if len(versions) < 2:
                continue
            versions.sort(key=lambda x: x['num'])
            last_version = versions[-1]
            for version in versions:
                if version['num'] == last_version['num']:
                    continue
                os.remove(version['path'])
            if last_version['num'] > 0:
                new_name = f"{base}{ext}"
                new_path = os.path.join(mods_folder, new_name)
                os.rename(last_version['path'], new_path)
                processed += 1

    version_mods, tag_name = get_latest_version_info("https://api.github.com/repos/SANTIK-Genius/mods/releases/latest")
    github_release_url = f'https://github.com/SANTIK-Genius/mods/releases/download/{version_mods}/mods.zip'

    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(github_release_url, headers=headers)

    # Путь к временному архиву
    temp_path = os.path.join(os.getenv("TEMP"), "mods.rar")

    print("Скачиваю моды...")
    response = urllib.request.urlopen(req)
    with open(temp_path, 'wb') as out_file:
        out_file.write(response.read())

    minecraft_mods = os.path.join(os.getenv('APPDATA'), '.minecraft', 'mods')
    if any(file.endswith(".jar") and file not in {"OptiFine-OptiFine-1.16.5_HD_U_G8_pre2.jar", "tl_skin_cape_forge_1.16.5-1.19.jar"} for file in os.listdir(minecraft_mods)):
        if input("Сделать чистую установку?(Удалить все моды) (y/n): ").strip().lower() == 'y':
            if input("ТОЧНО? (y/n): ").strip().lower() == 'y':
                if input("Сделать резерв копию? (y/n): ").strip().lower() == 'y':
                    while True:
                        backup_name = input("Введите имя резервной копии: ").strip()
                        if backup_name and not any(c in backup_name for c in r'\/:*?"<>|'):
                            break
                        print("СКАМ! ИМЯ НЕДОПУСТИМО! НЕ ОСТАВЛЯЙ ПУСТОЕ ПОЛЕ! И НЕЛЬЗЯ СИМВОЛЫ!!!")

                    backup_folder = os.path.join(minecraft_mods, "Резервные копии модов", backup_name)
                    if os.path.exists(backup_folder):
                        try:
                            shutil.rmtree(backup_folder)
                        except Exception as e:
                            print(f"Ошибка (СКАМ): {e}")
                    os.makedirs(backup_folder, exist_ok=True)

                    for file in os.listdir(minecraft_mods):
                        if file.endswith(".jar") and file not in {"OptiFine-OptiFine-1.16.5_HD_U_G8_pre2.jar", "tl_skin_cape_forge_1.16.5-1.19.jar"}:
                            source = os.path.join(minecraft_mods, file)
                            destination = os.path.join(backup_folder, file)
                            try:
                                shutil.move(source, destination)
                            except Exception as e:
                                print(f"Скам при резервировании файла {file}: {e}")
                    print(f"Резервная копия находится: {os.path.abspath(backup_folder)}")
                else:
                    print("Удаляю старые моды...")
                    for file in os.listdir(minecraft_mods):
                        if file.endswith(".jar") and file not in {"OptiFine-OptiFine-1.16.5_HD_U_G8_pre2.jar", "tl_skin_cape_forge_1.16.5-1.19.jar"}:
                            try:
                                os.remove(os.path.join(minecraft_mods, file))
                            except Exception as e:
                                print(f"Ошибка при удалении {file}: {e}")
    else:
        os.makedirs(minecraft_mods, exist_ok=True)

    # Распаковываем архив
    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
        zip_ref.extractall(minecraft_mods)
    process_mods_folder(minecraft_mods)

    os.remove(temp_path)
    print("Скачал! Успех!")

#Скачиваем ресурс паки
def download_resource_pack(pack):
    resourcepacks_dir = os.path.join(os.path.join(os.getenv("APPDATA"), ".minecraft"), "resourcepacks")
    os.makedirs(resourcepacks_dir, exist_ok=True)
    if pack == "required":
        version_mods, tag_name = get_latest_version_info("https://api.github.com/repos/SANTIK-Genius/resorce_pack/releases/latest")
        github_release_url = f'https://github.com/SANTIK-Genius/resorce_pack/releases/download/{version_mods}/from.YBER-slaves.zip'
        file_name = github_release_url.split("/")[-1]
        save_path = os.path.join(resourcepacks_dir, file_name)
        try:
            with urllib.request.urlopen(github_release_url) as response, open(save_path, 'wb') as out_file:
                out_file.write(response.read())
            print("УСТАНОВЛЕНО! (ПРОФИТ!)")
        except Exception as e:
            print(f"Ошибка при загрузке(Пизде): {e}")
    else:
        version_mods, tag_name = get_latest_version_info("https://api.github.com/repos/SANTIK-Genius/resorce_pack/releases/latest")
        github_release_url = f'https://github.com/SANTIK-Genius/resorce_pack/releases/download/{version_mods}/from.YBER-blocks.zip'
        file_name = github_release_url.split("/")[-1]
        save_path = os.path.join(resourcepacks_dir, file_name)
        try:
            with urllib.request.urlopen(github_release_url) as response, open(save_path, 'wb') as out_file:
                out_file.write(response.read())
            print("УСТАНОВЛЕНО! (УСПЕХ!)")
            print("HINT: Ставь from.YBER-blocks ниже from.YBER-slaves!!!")
        except Exception as e:
            print(f"Ошибка при загрузке(Пизде): {e}")
# Скачивание и установка zrok
def download_and_install_zrok(version, tag_name):
    zrok_filename = f"zrok_{version}_windows_amd64.tar.gz"
    zrok_url = f"https://github.com/openziti/zrok/releases/download/{tag_name}/{zrok_filename}"
    print("Скачивание:", zrok_url)
    urllib.request.urlretrieve(zrok_url, temp_tar_path)
    print("Скачано:", temp_tar_path)

    if not os.path.exists(minecraft_path):
        os.makedirs(minecraft_path)

    with tarfile.open(temp_tar_path, 'r:gz') as tar_ref:
        tar_ref.extractall(minecraft_path)

    os.remove(temp_tar_path)
    print("Установка завершена!")
    with open("join_server.bat", "w") as f:
        f.write("@echo off\n")
        f.write(f'{minecraft_path}/zrok.exe access private ever --bind 127.0.0.1:25565\n')
        f.write("pause\n")
    print("join_server.bat Создан!")
    output = subprocess.run([zrok_exe_path, "overview"], text=True, stderr=subprocess.DEVNULL,
                            stdout=subprocess.PIPE).stdout
    nbt_file = nbtlib.load(os.path.join(os.getenv("APPDATA"), ".minecraft", "servers.dat"))
    new_server = {
        'name': nbtlib.String("МЕГА СЕРВЕР EVER'a"),
        'ip': nbtlib.String('127.0.0.1:25565'),
        'acceptTextures': nbtlib.Byte(1)
    }
    servers_list = nbt_file['servers']

    servers_list[:] = [s for s in servers_list if s['ip'] != new_server['ip']]
    servers_list.insert(0, nbtlib.Compound(new_server))
    nbt_file.save()
    if "environments" in output:
        print("Zrok Enabled")
    else:
        while True:
            enable = input("Введи активатор ZROK: ")
            output = subprocess.run([zrok_exe_path, "enable", enable], text=True, stderr=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE).stdout
            if "the zrok environment was successfully enabled..." in output:
                print("Zrok Enabled!!!!!!")
                break
            else:
                print("Ввел не правильный ключ!")
    if input("Скачать моды?(y/n): ").lower() == "y":
        download_mods()
    if input("Скачать ОБЯЗАТЕЛЬНЫЙ ресурс пак?(y/n): ").lower() == "y":
        download_resource_pack("required")
    if input("Скачать ДОП ресурс пак?(y/n): ").lower() == "y":
        download_resource_pack("addon")
    show_menu()


def check_if_zrok_in_path():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Environment',
                            0, winreg.KEY_READ) as key:
            current_path, _ = winreg.QueryValueEx(key, "Path")
            if minecraft_path.lower() in current_path.lower():
                return True
    except:
        pass
    return False


def add_to_user_path(path):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Environment',
                            0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""
            if path.lower() not in current_path.lower():
                new_path = current_path + ";" + path if current_path else path
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                print("Путь добавлен в PATH")
    except Exception as e:
        print("Ошибка при добавлении в PATH:", e)


def get_local_zrok_version():
    try:
        output = os.popen(f'"{zrok_exe_path}" version').read().strip()
        last_line = output.strip().splitlines()[-1]
        return last_line.split()[0].lstrip("v")
    except:
        return None


# Главное меню
def show_menu():
    while True:
        print("\nМеню:")
        print("1. Присоединиться к сети zrok")
        print("2. Проверить обновления zrok/модов/ресурс паков")
        print("3. Переустановить zrok")
        print("4. Выйти")
        choice = input("Выберите опцию: ")
        if choice == "1":
            print("Запускаю...")
            appdata_path = os.getenv('APPDATA')
            zrok_path = os.path.join(appdata_path, '.minecraft', 'zrok', 'zrok.exe')
            command = [zrok_path, 'access', 'private', 'ever', '--bind', '127.0.0.1:25565']
            subprocess.run(['start', 'cmd', '/k'] + command, shell=True)
            print("Успешно запустил)")
            for i in range(5, 0, -1):
                print(f"Окно закроется через {i} секунд...", end="\r")
                time.sleep(1)
            sys.exit()
        if choice == "2":
            try:
                latest_version, tag = get_latest_version_info("https://api.github.com/repos/openziti/zrok/releases/latest")
                print(f"Последняя версия: {latest_version}")

                if not os.path.exists(zrok_exe_path):
                    print("zrok.exe не найден, скачиваем заново...")
                    download_and_install_zrok(latest_version, tag)
                    add_to_user_path(minecraft_path)
                    continue

                local_version = get_local_zrok_version()
                if local_version != latest_version:
                    print(f"Доступна новая версия: {latest_version}. Твоя версия: {local_version}. Обновление...")
                    download_and_install_zrok(latest_version, tag)
                else:
                    print("Установлена последняя версия.")
            except Exception as e:
                print("Ошибка при проверке обновлений:", e)
            if input("Обновить/скачать моды?(y/n): ").lower() == "y":
                download_mods()
            if input("Обновить/скачать ОБЯЗАТЕЛЬНЫЙ ресурс пак?(y/n): ").lower() == "y":
                download_resource_pack("required")
            if input("Обновить/скачать ДОП ресурс пак?(y/n): ").lower() == "y":
                download_resource_pack("addon")

        elif choice == "3":
            try:
                shutil.rmtree(minecraft_path, ignore_errors=True)
                latest_version, tag = get_latest_version_info()
                download_and_install_zrok(latest_version, tag)
                add_to_user_path(minecraft_path)
            except Exception as e:
                print("Ошибка при переустановке:", e)
        elif choice == "4":
            sys.exit()
        else:
            print("Неверный выбор. Повторите.")


if os.path.exists(zrok_exe_path):
    print("zrok уже установлен.")
    show_menu()
else:
    print("Установка zrok...")
    latest_version, tag = get_latest_version_info("https://api.github.com/repos/openziti/zrok/releases/latest")
    download_and_install_zrok(latest_version, tag)
    add_to_user_path(minecraft_path)

print("\nГотово!")

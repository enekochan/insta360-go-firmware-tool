#!/usr/bin/env python3
import os
import sys
import argparse
import textwrap
import io
import mmap
import tempfile
import zlib
import hashlib
import re
import shutil
# import mount

MD5_SIZE = 0x10  # 16
CRC32_SIZE = 0x04  # 4

HEADER_MAGIC_NUMBER = b'\xE6\xDF\x32\x87'
SECTION_MAGIC_NUMBER = b'\x90\xEB\x24\xA3'
RTOS_MAGIC_NUMBER = b'\x34\x00\x00\xEA\x05\x00\x00\xEA'
RTOS_MAGIC_NUMBER_POSITION = 0x00
ROMFS_MAGIC_NUMBER = b'\x8A\x32\xFC\x66'
ROMFS_MAGIC_NUMBER_POSITION = 0x00
KERNEL_MAGIC_NUMBER = b'\x41\x52\x4D\x64'  # ARMd
KERNEL_MAGIC_NUMBER_POSITION = 0x38
EXT2_MAGIC_NUMBER = b'\x53\xEF'
EXT2_MAGIC_NUMBER_POSITION = 0x438
DTB_MAGIC_NUMBER = b'\xD0\x0D\xFE\xED'
DTB_MAGIC_NUMBER_POSITION = 0x00

FIRMWARE_FOOTER_GO2_SIGNATURE = b'\x57\x46\x4E\x49\x54\x58\x4E\x4F\x02\x00\x00\x00\x00\x00\x00\x00'
FIRMWARE_FOOTER_GO3_SIGNATURE = b'\x57\x46\x4E\x49\x55\x58\x4E\x4F\x04\x00\x01\x00\x00\x00\x09\x00'
FIRMWARE_FOOTER_GO2_SIGNATURE_SIZE = len(FIRMWARE_FOOTER_GO2_SIGNATURE)
FIRMWARE_FOOTER_GO3_SIGNATURE_SIZE = len(FIRMWARE_FOOTER_GO3_SIGNATURE)

FIRMWARE_HEADER_NAME_POSITION = 0x00  # 0
FIRMWARE_HEADER_NAME_SIZE = 0x20  # 32
FIRMWARE_HEADER_MAGIC_NUMBER_POSITION = FIRMWARE_HEADER_NAME_POSITION + FIRMWARE_HEADER_NAME_SIZE  # 32
FIRMWARE_HEADER_MAGIC_NUMBER_SIZE = len(HEADER_MAGIC_NUMBER)  # 4
FIRMWARE_HEADER_CRC32_POSITION = FIRMWARE_HEADER_MAGIC_NUMBER_POSITION + FIRMWARE_HEADER_MAGIC_NUMBER_SIZE  # 36
FIRMWARE_HEADER_CRC32_SIZE = CRC32_SIZE  # 4
FIRMWARE_HEADER_ZEROS_POSITION = FIRMWARE_HEADER_CRC32_POSITION + FIRMWARE_HEADER_CRC32_SIZE  # 40
FIRMWARE_HEADER_ZEROS_SIZE = 0x08  # 8
FIRMWARE_HEADER_SECTIONS_TABLE_POSITION = FIRMWARE_HEADER_ZEROS_POSITION + FIRMWARE_HEADER_ZEROS_SIZE  # 48
FIRMWARE_HEADER_SECTIONS_COUNT = 0x10  # 16
FIRMWARE_HEADER_SECTIONS_SIZE = 0x08  # 8
FIRMWARE_HEADER_SECTIONS_LENGTH_SIZE = 0x04  # 4
FIRMWARE_HEADER_SECTIONS_CRC32_SIZE = CRC32_SIZE  # 4
FIRMWARE_HEADER_UNKNOWN_SIZE = 0x180  # 384
FIRMWARE_HEADER_SIZE = FIRMWARE_HEADER_NAME_SIZE +\
                        FIRMWARE_HEADER_MAGIC_NUMBER_SIZE +\
                        FIRMWARE_HEADER_CRC32_SIZE +\
                        FIRMWARE_HEADER_ZEROS_SIZE +\
                        FIRMWARE_HEADER_SECTIONS_COUNT * FIRMWARE_HEADER_SECTIONS_SIZE +\
                        FIRMWARE_HEADER_UNKNOWN_SIZE  # 560

SECTION_HEADER_CRC32_POSITION = 0x00  # 0
SECTION_HEADER_CRC32_SIZE = CRC32_SIZE  # 4
SECTION_HEADER_VERSION_POSITION = SECTION_HEADER_CRC32_POSITION + SECTION_HEADER_CRC32_SIZE  # 4
SECTION_HEADER_VERSION_SIZE = 0x04  # 4
SECTION_HEADER_DATE_POSITION = SECTION_HEADER_VERSION_POSITION + SECTION_HEADER_VERSION_SIZE  # 8
SECTION_HEADER_DATE_SIZE = 0x04  # 4
SECTION_HEADER_LENGTH_POSITION = SECTION_HEADER_DATE_POSITION + SECTION_HEADER_DATE_SIZE  # 12
SECTION_HEADER_LENGTH_SIZE = 0x04  # 4
SECTION_HEADER_LOADING_ADDRESS_POSITION = SECTION_HEADER_LENGTH_POSITION + SECTION_HEADER_LENGTH_SIZE  # 16
SECTION_HEADER_LOADING_ADDRESS_SIZE = 0x04  # 4
SECTION_HEADER_FLAGS_POSITION = SECTION_HEADER_LOADING_ADDRESS_POSITION + SECTION_HEADER_LOADING_ADDRESS_SIZE  # 20
SECTION_HEADER_FLAGS_SIZE = 0x04  # 4
SECTION_HEADER_MAGIC_NUMBER_POSITION = SECTION_HEADER_FLAGS_POSITION + SECTION_HEADER_FLAGS_SIZE  # 24
SECTION_HEADER_MAGIC_NUMBER_SIZE = 0x04  # 4
SECTION_HEADER_ZEROS_SIZE = 0xE4  # 228
SECTION_HEADER_SIZE = SECTION_HEADER_CRC32_SIZE +\
                       SECTION_HEADER_VERSION_SIZE +\
                       SECTION_HEADER_DATE_SIZE +\
                       SECTION_HEADER_LENGTH_SIZE +\
                       SECTION_HEADER_LOADING_ADDRESS_SIZE +\
                       SECTION_HEADER_FLAGS_SIZE +\
                       SECTION_HEADER_MAGIC_NUMBER_SIZE +\
                       SECTION_HEADER_ZEROS_SIZE  # 256

FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_POSITION = 0x00  # 0
FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_SIZE = 0x04  # 4
FIRMWARE_FOOTER_CAMERA_FILE_NAME_POSITION = FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_POSITION + FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_SIZE  # 4
FIRMWARE_FOOTER_CAMERA_FILE_NAME_SIZE = 0x20  # 32
FIRMWARE_FOOTER_CAMERA_VERSION_POSITION = FIRMWARE_FOOTER_CAMERA_FILE_NAME_POSITION + FIRMWARE_FOOTER_CAMERA_FILE_NAME_SIZE  # 36
FIRMWARE_FOOTER_CAMERA_VERSION_SIZE = 0x20  # 32
FIRMWARE_FOOTER_CAMERA_MD5_POSITION = FIRMWARE_FOOTER_CAMERA_VERSION_POSITION + FIRMWARE_FOOTER_CAMERA_VERSION_SIZE  # 68
FIRMWARE_FOOTER_CAMERA_MD5_SIZE = MD5_SIZE  # 16
FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_POSITION = FIRMWARE_FOOTER_CAMERA_MD5_POSITION + FIRMWARE_FOOTER_CAMERA_MD5_SIZE  # 84
FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_SIZE = 0x04  # 4
FIRMWARE_FOOTER_BOX_FILE_NAME_POSITION = FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_POSITION + FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_SIZE  # 88
FIRMWARE_FOOTER_BOX_FILE_NAME_SIZE = 0x20  # 32
FIRMWARE_FOOTER_BOX_VERSION_POSITION = FIRMWARE_FOOTER_BOX_FILE_NAME_POSITION + FIRMWARE_FOOTER_BOX_FILE_NAME_SIZE  # 120
FIRMWARE_FOOTER_BOX_VERSION_SIZE = 0x20  # 32
FIRMWARE_FOOTER_BOX_MD5_POSITION = FIRMWARE_FOOTER_BOX_VERSION_POSITION + FIRMWARE_FOOTER_BOX_VERSION_SIZE  # 152
FIRMWARE_FOOTER_BOX_MD5_SIZE = MD5_SIZE  # 16
FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FIRMWARE_LENGTH_POSITION = FIRMWARE_FOOTER_BOX_MD5_POSITION + FIRMWARE_FOOTER_BOX_MD5_SIZE  # 84
FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FIRMWARE_LENGTH_SIZE = 0x04  # 4
FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FILE_NAME_POSITION = FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FIRMWARE_LENGTH_POSITION + FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FIRMWARE_LENGTH_SIZE  # 88
FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FILE_NAME_SIZE = 0x20  # 32
FIRMWARE_FOOTER_CAMERA_BLUETOOTH_VERSION_POSITION = FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FILE_NAME_POSITION + FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FILE_NAME_SIZE  # 120
FIRMWARE_FOOTER_CAMERA_BLUETOOTH_VERSION_SIZE = 0x20  # 32
FIRMWARE_FOOTER_CAMERA_BLUETOOTH_MD5_POSITION = FIRMWARE_FOOTER_CAMERA_BLUETOOTH_VERSION_POSITION + FIRMWARE_FOOTER_CAMERA_BLUETOOTH_VERSION_SIZE  # 152
FIRMWARE_FOOTER_CAMERA_BLUETOOTH_MD5_SIZE = MD5_SIZE  # 16
FIRMWARE_FOOTER_BOX_BLUETOOTH_FIRMWARE_LENGTH_POSITION = FIRMWARE_FOOTER_CAMERA_BLUETOOTH_MD5_POSITION + FIRMWARE_FOOTER_CAMERA_BLUETOOTH_MD5_SIZE  # 84
FIRMWARE_FOOTER_BOX_BLUETOOTH_FIRMWARE_LENGTH_SIZE = 0x04  # 4
FIRMWARE_FOOTER_BOX_BLUETOOTH_FILE_NAME_POSITION = FIRMWARE_FOOTER_BOX_BLUETOOTH_FIRMWARE_LENGTH_POSITION + FIRMWARE_FOOTER_BOX_BLUETOOTH_FIRMWARE_LENGTH_SIZE  # 88
FIRMWARE_FOOTER_BOX_BLUETOOTH_FILE_NAME_SIZE = 0x20  # 32
FIRMWARE_FOOTER_BOX_BLUETOOTH_VERSION_POSITION = FIRMWARE_FOOTER_BOX_BLUETOOTH_FILE_NAME_POSITION + FIRMWARE_FOOTER_BOX_BLUETOOTH_FILE_NAME_SIZE  # 120
FIRMWARE_FOOTER_BOX_BLUETOOTH_VERSION_SIZE = 0x20  # 32
FIRMWARE_FOOTER_BOX_BLUETOOTH_MD5_POSITION = FIRMWARE_FOOTER_BOX_BLUETOOTH_VERSION_POSITION + FIRMWARE_FOOTER_BOX_BLUETOOTH_VERSION_SIZE  # 152
FIRMWARE_FOOTER_BOX_BLUETOOTH_MD5_SIZE = MD5_SIZE  # 16

FIRMWARE_FOOTER_GO2_SIZE = FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_FILE_NAME_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_VERSION_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_MD5_SIZE +\
                        FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_SIZE +\
                        FIRMWARE_FOOTER_BOX_FILE_NAME_SIZE +\
                        FIRMWARE_FOOTER_BOX_VERSION_SIZE +\
                        FIRMWARE_FOOTER_BOX_MD5_SIZE +\
                        FIRMWARE_FOOTER_GO2_SIGNATURE_SIZE  # 184

FIRMWARE_FOOTER_GO3_SIZE = FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_FILE_NAME_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_VERSION_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_MD5_SIZE +\
                        FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_SIZE +\
                        FIRMWARE_FOOTER_BOX_FILE_NAME_SIZE +\
                        FIRMWARE_FOOTER_BOX_VERSION_SIZE +\
                        FIRMWARE_FOOTER_BOX_MD5_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FIRMWARE_LENGTH_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FILE_NAME_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_BLUETOOTH_VERSION_SIZE +\
                        FIRMWARE_FOOTER_CAMERA_BLUETOOTH_MD5_SIZE +\
                        FIRMWARE_FOOTER_BOX_BLUETOOTH_FIRMWARE_LENGTH_SIZE +\
                        FIRMWARE_FOOTER_BOX_BLUETOOTH_FILE_NAME_SIZE +\
                        FIRMWARE_FOOTER_BOX_BLUETOOTH_VERSION_SIZE +\
                        FIRMWARE_FOOTER_BOX_BLUETOOTH_MD5_SIZE +\
                        FIRMWARE_FOOTER_GO3_SIGNATURE_SIZE  # 352

ROMFS_HEADER_SIZE = 0x0000A000  # 40960
ROMFS_FILECOUNT_POSITION = len(ROMFS_MAGIC_NUMBER)  # 4
ROMFS_FILECOUNT_SIZE = 0x04
ROMFS_FILE_FILENAME_POSITION = 0x00
ROMFS_FILE_FILENAME_SIZE = 0x40  # 64
ROMFS_FILE_LENGTH_POSITION = ROMFS_FILE_FILENAME_POSITION + ROMFS_FILE_FILENAME_SIZE
ROMFS_FILE_LENGTH_SIZE = 0x04
ROMFS_FILE_OFFSET_POSITION = ROMFS_FILE_LENGTH_POSITION + ROMFS_FILE_LENGTH_SIZE
ROMFS_FILE_OFFSET_SIZE = 0x04
ROMFS_FILE_CRC32_POSITION = ROMFS_FILE_OFFSET_POSITION + ROMFS_FILE_OFFSET_SIZE
ROMFS_FILE_CRC32_SIZE = CRC32_SIZE
ROMFS_FILE_ENTRY_SIZE = ROMFS_FILE_FILENAME_SIZE + ROMFS_FILE_LENGTH_SIZE + ROMFS_FILE_OFFSET_SIZE + ROMFS_FILE_CRC32_SIZE  # File name length plus file size, file offset and crc32 = 76
ROMFS_MAX_FILE_COUNT = int(ROMFS_HEADER_SIZE / ROMFS_FILE_ENTRY_SIZE // 1)  # 40960 header size divided by 64+4+4+4 entry per file in header and rounded down = 538


def read(f, offset, length):
    f.seek(offset)
    return f.read(length)


def write(file_path, content, offset=0):
    file = open(file_path, 'wb')
    file.seek(offset)
    file.write(content)
    file.close()


def append_line(file_path, content):
    file = open(file_path, 'a')
    file.write(content + '\n')
    file.close()


def calculate_md5(f, start, length):
    f.seek(start)
    content = f.read(length)
    return hashlib.md5(content).digest()


def calculate_crc32(f, start, length, value=0):
    f.seek(start)
    content = f.read(length)
    return zlib.crc32(content, value).to_bytes(CRC32_SIZE, 'little')


class HeaderSection:
    def __init__(self, start, end, length, crc32, crc32_inverse):
        self.start = start
        self.end = end
        self.length = length
        self.crc32 = crc32
        self.crc32_inverse = crc32_inverse


class Section:
    def __init__(self, number, start, end, crc32, version, date, length, loading_address, flags, magic_number):
        self.number = number
        self.start = start
        self.end = end
        self.crc32 = crc32
        self.version = version
        self.date = date
        self.length = length
        self.loading_address = loading_address
        self.flags = flags
        self.magic_number = magic_number


class Box:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class RomFs:
    def __init__(self):
        self.files = []

    def add_file(self, file_name, content):
        self.files.append([file_name, content])

    def remove_file(self, file_name):
        for index, f in self.files:
            if f[0] == file_name:
                self.files.pop(index)
                break

    def remove_files(self):
        self.files.clear()

    def extract(self, origin, destiny):
        romfs = open(origin, 'r+b')
        romfs_mm = mmap.mmap(romfs.fileno(), 0)
        romfs_mm.seek(0)
        romfs_magic_number = read(romfs_mm, ROMFS_MAGIC_NUMBER_POSITION, len(ROMFS_MAGIC_NUMBER))
        if romfs_magic_number != ROMFS_MAGIC_NUMBER:
            print('Invalid ROMFS magic number detected, skipping...')
        else:
            print('Detected ROMFS section, unpacking...')
            romfs_file_count = read(romfs_mm, ROMFS_FILECOUNT_POSITION, ROMFS_FILECOUNT_SIZE)
            romfs_file_count = int.from_bytes(romfs_file_count, 'little')
            print('ROMFS contains ' + str(romfs_file_count) + ' files')
            os.mkdir(destiny)
            for j in range(0, romfs_file_count):
                file_entry_base_position = (len(ROMFS_MAGIC_NUMBER) + ROMFS_FILECOUNT_SIZE) + j * ROMFS_FILE_ENTRY_SIZE
                file_name = read(romfs_mm, file_entry_base_position + ROMFS_FILE_FILENAME_POSITION, ROMFS_FILE_FILENAME_SIZE).decode('utf-8').rstrip('\0')
                # print('Extracting ' + file_name)
                file_length = int.from_bytes(
                    read(romfs_mm, file_entry_base_position + ROMFS_FILE_LENGTH_POSITION, ROMFS_FILE_LENGTH_SIZE), 'little')
                file_offset = int.from_bytes(
                    read(romfs_mm, file_entry_base_position + ROMFS_FILE_OFFSET_POSITION, ROMFS_FILE_OFFSET_SIZE), 'little')
                file_crc32 = read(romfs_mm, file_entry_base_position + ROMFS_FILE_CRC32_POSITION, ROMFS_FILE_CRC32_SIZE)
                file_content = read(romfs_mm, file_offset, file_length)
                file_content_crc32 = calculate_crc32(romfs_mm, file_offset, file_length)
                if file_crc32 != file_content_crc32:
                    print('Invalid file CRC32, skipping...')
                    continue
                write(destiny + os.sep + file_name, file_content)
                append_line(destiny + '.files', file_name)
        romfs.close()

    def write_files(self, files_list_file):
        self.remove_files()
        files_file = open(files_list_file, 'r')
        files = files_file.readlines()
        folder = os.path.dirname(os.path.abspath(files_list_file))
        section_name = os.path.splitext(os.path.basename(files_list_file))[0]
        for file_name in files:
            file_name = file_name.strip()
            # print(file_name)
            file = open(folder + os.sep + section_name + os.sep + file_name, 'rb')
            self.add_file(file_name, file.read())
            file.close()
        files_file.close()
        self.write(folder + os.sep + section_name + '.bin')

    def write(self, output):
        # Check file count is not more than 538
        if len(self.files) > ROMFS_MAX_FILE_COUNT:
            print('Too much files. Max file count is {:d}'.format(ROMFS_MAX_FILE_COUNT))
            return

        # Check file names are max 64 characters in length
        for f in self.files:
            if len(f[0]) > ROMFS_FILE_FILENAME_SIZE:
                print('File name {} too long. Max file name length is {:d}'.format(f[1], ROMFS_FILE_FILENAME_SIZE))
                return

        # Create ROMFS header
        output_file = open(output, 'wb')
        output_file.write(ROMFS_MAGIC_NUMBER)
        output_file.write(len(self.files).to_bytes(ROMFS_FILECOUNT_SIZE, 'little'))
        file_offset = ROMFS_HEADER_SIZE  # First file offset is header size
        for f in self.files:
            # File name with leading nulls up to 64 characters
            file_name = f[0] + ('\0' * (ROMFS_FILE_FILENAME_SIZE - len(f[0])))
            output_file.write(bytes(file_name, encoding='utf8'))
            # File size
            file_size = len(f[1])
            output_file.write(file_size.to_bytes(ROMFS_FILE_LENGTH_SIZE, 'little'))
            # File data offset
            output_file.write(file_offset.to_bytes(ROMFS_FILE_OFFSET_SIZE, 'little'))
            file_offset += file_size  # Prepare the offset for next file with current file size plus previous offset
            file_offset += 2048 - (file_size % 2048)  # Round to the next 2048 block
            # File CRC32
            file_crc32 = zlib.crc32(f[1], 0)
            output_file.write(file_crc32.to_bytes(ROMFS_FILE_CRC32_SIZE, 'little'))
        header_leading_null = '\0' * (ROMFS_HEADER_SIZE - (8 + len(self.files) * ROMFS_FILE_ENTRY_SIZE))
        output_file.write(bytes(header_leading_null, encoding='utf8'))
        # Write ROMFS content with files content
        for f in self.files:
            file_content = f[1]
            output_file.write(file_content)
            # Add leading nulls to fill the block up to 2048 bytes
            file_size = len(f[1])
            amount = 2048 - (file_size % 2048)
            output_file.write(bytes('\0' * amount, encoding='utf8'))
        output_file.close()


class Firmware:
    firmware_path = None
    file_size = 0
    fw = None
    mm = None
    firmware_header_name = ''
    firmware_header_magic_number = None
    firmware_header_crc32 = None
    firmware_header_zeros = None
    header_sections = None
    sections = None
    is_go2 = False
    is_go3 = False
    footer_size = 0
    camera_firmware_middle_md5 = None
    camera_firmware_size = None
    camera_firmware_filename = None
    camera_firmware_version = None
    camera_firmware_footer_md5 = None
    camera_bluetooth_firmware_size = None
    camera_bluetooth_firmware_filename = None
    camera_bluetooth_firmware_version = None
    camera_bluetooth_firmware_footer_md5 = None
    box_firmware_size = None
    box_firmware_filename = None
    box_firmware_version = None
    box_firmware_footer_md5 = None
    box_bluetooth_firmware_size = None
    box_bluetooth_firmware_filename = None
    box_bluetooth_firmware_version = None
    box_bluetooth_firmware_footer_md5 = None

    def __init__(self, firmware_path):
        self.firmware_path = firmware_path
        if os.path.exists(firmware_path):
            self.file_size = os.path.getsize(self.firmware_path)
            self.fw = open(self.firmware_path, 'r+b')
            self.mm = mmap.mmap(self.fw.fileno(), 0)
            self.mm.seek(0)
            self.sections = []
            self.header_sections = []
            self.get_insta360_go_version()
            self.read_header()
            self.read_footer()
            self.read_middle_md5()

    def __del__(self):
        if self.fw is not None:
            self.fw.close()

    def get_insta360_go_version(self):
        # Is it a Insta360 GO 2 firmware?
        footer_signature = read(self.mm, self.file_size - FIRMWARE_FOOTER_GO2_SIGNATURE_SIZE, FIRMWARE_FOOTER_GO2_SIGNATURE_SIZE)
        if footer_signature == FIRMWARE_FOOTER_GO2_SIGNATURE:
            self.is_go2 = True
            self.footer_size = FIRMWARE_FOOTER_GO2_SIZE
        # Is it a Insta360 GO 3 firmware?
        footer_signature = read(self.mm, self.file_size - FIRMWARE_FOOTER_GO3_SIGNATURE_SIZE, FIRMWARE_FOOTER_GO3_SIGNATURE_SIZE)
        if footer_signature == FIRMWARE_FOOTER_GO3_SIGNATURE:
            self.is_go3 = True
            self.footer_size = FIRMWARE_FOOTER_GO3_SIZE
        # Is it none?
        if not self.is_go2 and not self.is_go3:
            print('Only Insta360 GO 2 and Insta360 GO 3 cameras are supported')
            sys.exit(1)

    def read_header(self):
        self.firmware_header_name = read(self.mm, FIRMWARE_HEADER_NAME_POSITION, FIRMWARE_HEADER_NAME_SIZE).decode('utf-8').rstrip('\0')
        self.firmware_header_magic_number = read(self.mm, FIRMWARE_HEADER_MAGIC_NUMBER_POSITION, FIRMWARE_HEADER_MAGIC_NUMBER_SIZE)
        self.firmware_header_crc32 = read(self.mm, FIRMWARE_HEADER_CRC32_POSITION, FIRMWARE_HEADER_CRC32_SIZE)
        self.firmware_header_zeros = read(self.mm, FIRMWARE_HEADER_ZEROS_POSITION, FIRMWARE_HEADER_ZEROS_SIZE)
        self.read_header_sections()

    def read_header_sections(self):
        start = FIRMWARE_HEADER_SIZE
        end = 0
        for i in range(0, FIRMWARE_HEADER_SECTIONS_COUNT):
            # Section length
            section_length = read(self.mm,
                                  FIRMWARE_HEADER_SECTIONS_TABLE_POSITION + i * FIRMWARE_HEADER_SECTIONS_SIZE,
                                  FIRMWARE_HEADER_SECTIONS_LENGTH_SIZE)
            # Section crc32
            section_crc32 = read(self.mm,
                                 FIRMWARE_HEADER_SECTIONS_TABLE_POSITION + i * FIRMWARE_HEADER_SECTIONS_SIZE + FIRMWARE_HEADER_SECTIONS_LENGTH_SIZE,
                                 FIRMWARE_HEADER_SECTIONS_CRC32_SIZE)
            # CRC32 has to be inverted to compare it later with running CRC32 (a running CRC32 uses the previous CRC32 as base value)
            section_crc32_inverse = 0xffffffff ^ int.from_bytes(section_crc32, 'big')
            section_crc32_inverse = section_crc32_inverse.to_bytes(FIRMWARE_HEADER_SECTIONS_CRC32_SIZE, 'little')

            # The section 5 has crc32 but no length, so we get it from the section's header itself
            if section_crc32 != b'\x00\x00\x00\x00' and section_length == b'\x00\x00\x00\x00':
                offset = self.mm.find(SECTION_MAGIC_NUMBER, end)
                section_length = read(self.mm,
                                      offset - (SECTION_HEADER_CRC32_SIZE + SECTION_HEADER_VERSION_SIZE + SECTION_HEADER_DATE_SIZE),
                                      SECTION_HEADER_LENGTH_SIZE)
                section_length = int.from_bytes(section_length, 'little') + SECTION_HEADER_SIZE  # The length in the section header does not count the header itself
                section_length = section_length.to_bytes(SECTION_HEADER_LENGTH_SIZE, 'little')

            end = start + int.from_bytes(section_length, 'little')

            # Store the section's data for later
            if section_crc32 != b'\x00\x00\x00\x00' and section_length != b'\x00\x00\x00\x00':
                header_section = HeaderSection(start, end, section_length, section_crc32, section_crc32_inverse)
                self.header_sections.append(header_section)

            if section_length.hex() != '00000000':
                # Store section header
                crc32 = read(self.mm, start + SECTION_HEADER_CRC32_POSITION, SECTION_HEADER_CRC32_SIZE)
                version = read(self.mm, start + SECTION_HEADER_VERSION_POSITION, SECTION_HEADER_VERSION_SIZE)
                date = read(self.mm, start + SECTION_HEADER_DATE_POSITION, SECTION_HEADER_DATE_SIZE)
                length = read(self.mm, start + SECTION_HEADER_LENGTH_POSITION, SECTION_HEADER_LENGTH_SIZE)
                loading_address = read(self.mm, start + SECTION_HEADER_LOADING_ADDRESS_POSITION, SECTION_HEADER_LOADING_ADDRESS_SIZE)
                flags = read(self.mm, start + SECTION_HEADER_FLAGS_POSITION, SECTION_HEADER_FLAGS_SIZE)
                magic_number = read(self.mm, start + SECTION_HEADER_MAGIC_NUMBER_POSITION, SECTION_HEADER_MAGIC_NUMBER_SIZE)
                self.sections.append(Section(i, start + SECTION_HEADER_SIZE, end, crc32, version, date, length, loading_address, flags, magic_number))

            start = end

    def read_middle_md5(self):
        # There is an MD5 hash of the camera firmware between the camera and the box firmware
        self.camera_firmware_middle_md5 = read(self.mm, self.camera_firmware_size - MD5_SIZE, MD5_SIZE)
        print(self.camera_firmware_middle_md5.hex())

    def read_footer(self):
        # Get camera and box firmware size from the footer
        self.camera_firmware_size = int.from_bytes(
            read(self.mm,
                 self.file_size - self.footer_size + FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_POSITION,
                 FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_SIZE), 'little')
        self.box_firmware_size = int.from_bytes(
            read(self.mm,
                 self.file_size - self.footer_size + FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_POSITION,
                 FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_SIZE), 'little')
        if self.is_go3:
            self.camera_bluetooth_firmware_size = int.from_bytes(
                read(self.mm,
                     self.file_size - self.footer_size + FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FIRMWARE_LENGTH_POSITION,
                     FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FIRMWARE_LENGTH_SIZE), 'little')
            self.box_bluetooth_firmware_size = int.from_bytes(
                read(self.mm,
                     self.file_size - self.footer_size + FIRMWARE_FOOTER_BOX_BLUETOOTH_FIRMWARE_LENGTH_POSITION,
                     FIRMWARE_FOOTER_BOX_BLUETOOTH_FIRMWARE_LENGTH_SIZE), 'little')
        else:
            self.camera_bluetooth_firmware_size = 0
            self.box_bluetooth_firmware_size = 0

        print('Camera firmware size: ' + str(self.camera_firmware_size))
        print('Box firmware size: ' + str(self.box_firmware_size))
        if self.is_go3:
            print('Camera Bluetooth firmware size: ' + str(self.camera_bluetooth_firmware_size))
            print('Box Bluetooth firmware size: ' + str(self.box_bluetooth_firmware_size))
        print('Footer size: ' + str(self.footer_size))
        print('Total size: ' + str(self.camera_firmware_size + self.box_firmware_size + self.camera_bluetooth_firmware_size + self.box_bluetooth_firmware_size + self.footer_size))

        self.camera_firmware_filename = read(self.mm,
                                             self.file_size - self.footer_size + FIRMWARE_FOOTER_CAMERA_FILE_NAME_POSITION,
                                             FIRMWARE_FOOTER_CAMERA_FILE_NAME_SIZE)
        print(self.camera_firmware_filename.decode('utf-8').rstrip('\0'))
        self.camera_firmware_version = read(self.mm,
                                            self.file_size - self.footer_size + FIRMWARE_FOOTER_CAMERA_VERSION_POSITION,
                                            FIRMWARE_FOOTER_CAMERA_VERSION_SIZE)
        print(self.camera_firmware_version.decode('utf-8').rstrip('\0'))
        self.camera_firmware_footer_md5 = read(self.mm,
                                               self.file_size - self.footer_size + FIRMWARE_FOOTER_CAMERA_MD5_POSITION,
                                               FIRMWARE_FOOTER_CAMERA_MD5_SIZE)
        print(self.camera_firmware_footer_md5.hex())

        self.box_firmware_filename = read(self.mm,
                                          self.file_size - self.footer_size + FIRMWARE_FOOTER_BOX_FILE_NAME_POSITION,
                                          FIRMWARE_FOOTER_BOX_FILE_NAME_SIZE)
        print(self.box_firmware_filename.decode('utf-8').rstrip('\0'))
        self.box_firmware_version = read(self.mm,
                                         self.file_size - self.footer_size + FIRMWARE_FOOTER_BOX_VERSION_POSITION,
                                         FIRMWARE_FOOTER_BOX_VERSION_SIZE)
        print(self.box_firmware_version.decode('utf-8').rstrip('\0'))
        self.box_firmware_footer_md5 = read(self.mm,
                                            self.file_size - self.footer_size + FIRMWARE_FOOTER_BOX_MD5_POSITION,
                                            FIRMWARE_FOOTER_BOX_MD5_SIZE)
        print(self.box_firmware_footer_md5.hex())

        if self.is_go3:
            self.camera_bluetooth_firmware_filename = read(self.mm,
                                                 self.file_size - self.footer_size + FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FILE_NAME_POSITION,
                                                 FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FILE_NAME_SIZE)
            print(self.camera_bluetooth_firmware_filename.decode('utf-8').rstrip('\0'))
            self.camera_bluetooth_firmware_version = read(self.mm,
                                                self.file_size - self.footer_size + FIRMWARE_FOOTER_CAMERA_BLUETOOTH_VERSION_POSITION,
                                                FIRMWARE_FOOTER_CAMERA_BLUETOOTH_VERSION_SIZE)
            print(self.camera_bluetooth_firmware_version.decode('utf-8').rstrip('\0'))
            self.camera_bluetooth_firmware_footer_md5 = read(self.mm,
                                                   self.file_size - self.footer_size + FIRMWARE_FOOTER_CAMERA_BLUETOOTH_MD5_POSITION,
                                                   FIRMWARE_FOOTER_CAMERA_BLUETOOTH_MD5_SIZE)
            print(self.camera_bluetooth_firmware_footer_md5.hex())

            self.box_bluetooth_firmware_filename = read(self.mm,
                                              self.file_size - self.footer_size + FIRMWARE_FOOTER_BOX_BLUETOOTH_FILE_NAME_POSITION,
                                              FIRMWARE_FOOTER_BOX_BLUETOOTH_FILE_NAME_SIZE)
            print(self.box_bluetooth_firmware_filename.decode('utf-8').rstrip('\0'))
            self.box_bluetooth_firmware_version = read(self.mm,
                                             self.file_size - self.footer_size + FIRMWARE_FOOTER_BOX_BLUETOOTH_VERSION_POSITION,
                                             FIRMWARE_FOOTER_BOX_BLUETOOTH_VERSION_SIZE)
            print(self.box_bluetooth_firmware_version.decode('utf-8').rstrip('\0'))
            self.box_bluetooth_firmware_footer_md5 = read(self.mm,
                                                self.file_size - self.footer_size + FIRMWARE_FOOTER_BOX_BLUETOOTH_MD5_POSITION,
                                                FIRMWARE_FOOTER_BOX_BLUETOOTH_MD5_SIZE)
            print(self.box_bluetooth_firmware_footer_md5.hex())

    def validate(self):
        sections_running_crc32 = bytes(0x0)
        for i in range(0, len(self.header_sections)):
            header_section = self.header_sections[i]
            start = header_section.start
            # end = header_section.end
            section_length = header_section.length
            section_crc32 = header_section.crc32
            section_crc32_inverse = header_section.crc32_inverse

            # A running CRC32 uses the previous CRC32 as base value
            sections_running_crc32 = calculate_crc32(self.mm,
                                                     start,
                                                     int.from_bytes(section_length, 'little'),
                                                     int.from_bytes(sections_running_crc32, 'little'))

            if section_crc32.hex() != '00000000':
                section_crc32_formatted = '0x{:08x}'.format(int.from_bytes(section_crc32, 'big'))
                section_crc32_inverse_formatted = '0x{:08x}'.format(int.from_bytes(section_crc32_inverse, 'big'))
                section_running_crc32_formatted = '0x{:08x}'.format(int.from_bytes(sections_running_crc32, 'little'))
                section_length_formatted = '0x{:08x}'.format(int.from_bytes(section_length, 'big'))
                print('Section ' + str(i) +
                      ' crc32 read: ' + section_crc32_formatted +
                      ' - crc32 inverse: ' + section_crc32_inverse_formatted +
                      ' - crc32 running: ' + section_running_crc32_formatted +
                      ' - length: ' + section_length_formatted + ' (' + str(int.from_bytes(section_length, 'little')) + ' bytes)')
                if section_crc32_inverse_formatted != section_running_crc32_formatted:
                    print('Invalid CRC32 in firmware header for section {:d}'.format(i))
                    exit(1)

            if section_length.hex() != '00000000':
                # Check CRC32 for section content
                crc32 = self.sections[i].crc32
                calculated_crc32 = calculate_crc32(self.mm,
                                                   start + SECTION_HEADER_SIZE,
                                                   int.from_bytes(section_length, 'little') - SECTION_HEADER_SIZE)
                if calculated_crc32 != crc32:
                    print('Invalid CRC32 for content in section {:d}'.format(i))
                    exit(1)

        # Check the sizes of the firmwares and the footer add up to the actual file size
        if self.camera_firmware_size + self.box_firmware_size + self.camera_bluetooth_firmware_size + self.box_bluetooth_firmware_size + self.footer_size != self.file_size:
            print('Invalid file size')
            exit(1)

        if self.firmware_header_name != '':
            print('Invalid firmware header name')
            exit(1)

        if self.firmware_header_magic_number != HEADER_MAGIC_NUMBER:
            print('Invalid firmware header magic number')
            exit(1)

        # Check the firmware header CRC32
        firmware_crc32 = read(self.mm, FIRMWARE_HEADER_CRC32_POSITION, FIRMWARE_HEADER_CRC32_SIZE)
        # print(firmware_crc32.hex())
        # Calculate the CRC32 from where the firmware header ends up to the end of the camera firmware (without the MD5 at the end)
        firmware_crc32_calculated = calculate_crc32(self.mm,
                                                    FIRMWARE_HEADER_SIZE,
                                                    self.camera_firmware_size - FIRMWARE_HEADER_SIZE - MD5_SIZE)
        # print(firmware_crc32_calculated.hex())
        if firmware_crc32.hex() != firmware_crc32_calculated.hex():
            print('Invalid firmware header CRC32')
            exit(1)

        if self.firmware_header_zeros.decode('utf-8').rstrip('\0') != '':
            print('Invalid firmware header zeros')
            exit(1)

        # Check that the firmware ends with an appropriate signature
        if self.is_go2 is False and self.is_go3 is False:
            print('Invalid footer signature')
            exit(1)

        # Check the camera firmware internal MD5
        camera_firmware_middle_md5_calculated = calculate_md5(self.mm, 0x0, self.camera_firmware_size - MD5_SIZE)
        if self.camera_firmware_middle_md5 != camera_firmware_middle_md5_calculated:
            print('Invalid camera firmware internal MD5')
            exit(1)

        # Check the camera firmware MD5
        camera_firmware_footer_md5_calculated = calculate_md5(self.mm, 0x0, self.camera_firmware_size)
        if self.camera_firmware_footer_md5 != camera_firmware_footer_md5_calculated:
            print('Invalid camera firmware MD5')
            exit(1)

        # Check the box firmware MD5
        box_firmware_footer_md5_calculated = calculate_md5(self.mm, self.camera_firmware_size, self.box_firmware_size)
        if self.box_firmware_footer_md5 != box_firmware_footer_md5_calculated:
            print('Invalid box firmware MD5')
            exit(1)

        if self.is_go3 is True:
            # Check the camera bluetooth firmware MD5
            camera_bluetooth_firmware_footer_md5_calculated = calculate_md5(self.mm, self.camera_firmware_size + self.box_firmware_size, self.camera_bluetooth_firmware_size)
            if self.camera_bluetooth_firmware_footer_md5 != camera_bluetooth_firmware_footer_md5_calculated:
                print('Invalid camera bluetooth firmware MD5')
                exit(1)

            # Check the box bluetooth firmware MD5
            box_bluetooth_firmware_footer_md5_calculated = calculate_md5(self.mm, self.camera_firmware_size + self.box_firmware_size + self.camera_bluetooth_firmware_size, self.box_bluetooth_firmware_size)
            if self.box_bluetooth_firmware_footer_md5 != box_bluetooth_firmware_footer_md5_calculated:
                print('Invalid box bluetooth firmware MD5')
                exit(1)

        print('Firmware OK!')

        return 0

    def unpack(self, folder):
        print('Unpacking...')
        os.mkdir(folder)

        # Sections from header
        for i in range(0, len(self.sections)):
            print('Exporting section ' + str(i))
            content = read(self.mm, self.sections[i].start - SECTION_HEADER_SIZE, SECTION_HEADER_SIZE)
            write(folder + os.sep + 'section_' + str(i) + '.header', content)
            content = read(self.mm, self.sections[i].start, int.from_bytes(self.sections[i].length, 'little'))
            write(folder + os.sep + 'section_' + str(i) + '.bin', content)
            if content.startswith(ROMFS_MAGIC_NUMBER):
                romfs = RomFs()
                origin = folder + os.sep + 'section_' + str(i) + '.bin'
                destiny = folder + os.sep + 'section_' + str(i)
                romfs.extract(origin, destiny)
            elif content.startswith(DTB_MAGIC_NUMBER):
                print('Detected DTB section...')
                # args = type('args', (object,), {'extract': True, 'filename': os.getcwd() + os.sep + 'section_' + str(i) + '.bin', 'output_dir': 'dtb'})()
                # extract_dtb.split(args)
                if shutil.which('dtc') is not None:
                    print('Unpacking dtb...')
                    os.system('dtc -q -I dtb -O dts -o - ' + folder + os.sep + 'section_' + str(i) + '.bin' + ' > ' + folder + os.sep + 'section_' + str(i) + '.dts')
                else:
                    print('device-tree-compiler is not installed, skipping...')
            elif content[EXT2_MAGIC_NUMBER_POSITION:EXT2_MAGIC_NUMBER_POSITION+len(EXT2_MAGIC_NUMBER)] == EXT2_MAGIC_NUMBER:
                print('Detected Linux EXT2 filesystem section... ')
                # if sys.platform == 'linux' or sys.platform == 'linux2':
                #     print('Mounting...')
                #     if os.path.exists(folder + os.sep + 'section_' + str(i) + '.ext2'):
                #         print('section_' + str(i) + '.ext2 folder already exists, mount skipped...')
                #     else:
                #         os.mkdir(folder + os.sep + 'section_' + str(i) + '.ext2')
                #         # os.system('sudo mount -o rw,loop ' + 'section_' + str(i) + '.bin ' + folder + os.sep + 'section_' + str(i) + '.ext2')
                #         mount.mount(folder + os.sep + 'section_' + str(i) + '.bin', folder + os.sep + 'section_' + str(i) + '.ext2', 'ext2', 'rw')
                # else:
                #     print('Non Linux system detected, mount skipped...')

        # Firmware header
        firmware_header = read(self.mm, 0, FIRMWARE_HEADER_SIZE)
        write(folder + os.sep + 'firmware.header', firmware_header)

        # Firmware footer
        footer = read(self.mm, self.file_size - self.footer_size, self.footer_size)
        write(folder + os.sep + 'firmware.footer', footer)

        # Box firmware
        firmware_box = read(self.mm, self.camera_firmware_size, self.box_firmware_size)
        write(folder + os.sep + 'box.bin', firmware_box)

        if self.is_go3:
            # Camera Bluetooth Firmware
            firmware_camera_bt = read(self.mm, self.camera_firmware_size + self.box_firmware_size, self.camera_bluetooth_firmware_size)
            write(folder + os.sep + 'camera_bt.bin', firmware_camera_bt)

            # Box Bluetooth Firmware
            firmware_box_bt = read(self.mm, self.camera_firmware_size + self.box_firmware_size + self.camera_bluetooth_firmware_size, self.box_bluetooth_firmware_size)
            write(folder + os.sep + 'box_bt.bin', firmware_box_bt)

    def pack(self, folder):
        print('Packing...')

        # Get camera version from footer file
        footer_file_size = os.path.getsize(folder + os.sep + 'firmware.footer')
        footer_file = open(folder + os.sep + 'firmware.footer', 'r+b')
        # Is it a Insta360 GO 2 firmware?
        footer_file.seek(footer_file_size - FIRMWARE_FOOTER_GO2_SIGNATURE_SIZE)
        footer_signature = footer_file.read(FIRMWARE_FOOTER_GO2_SIGNATURE_SIZE)
        if footer_signature == FIRMWARE_FOOTER_GO2_SIGNATURE:
            self.is_go2 = True
        # Is it a Insta360 GO 3 firmware?
        footer_file.seek(footer_file_size - FIRMWARE_FOOTER_GO3_SIGNATURE_SIZE)
        footer_signature = footer_file.read(FIRMWARE_FOOTER_GO3_SIGNATURE_SIZE)
        if footer_signature == FIRMWARE_FOOTER_GO3_SIGNATURE:
            self.is_go3 = True
        # Is it none?
        if self.is_go2 is False and self.is_go3 is False:
            print('Only Insta360 GO 2 and Insta360 GO 3 cameras are supported')
            sys.exit(1)
        footer_file.close()

        # Get sections from folder and order them
        self.sections = [f for f in os.listdir(folder) if re.match(r'section_[0-9]+\.bin', f)]
        self.sections.sort()

        temp_directory = tempfile.mkdtemp()
        total_size = 0

        print('Backing up section data...')
        for i in range(0, len(self.sections)):
            section_file = open(folder + os.sep + self.sections[i], 'rb')
            if read(section_file, RTOS_MAGIC_NUMBER_POSITION, len(RTOS_MAGIC_NUMBER)) == RTOS_MAGIC_NUMBER:
                print(self.sections[i] + ': RTOS')
                # Nothing
            elif read(section_file, ROMFS_MAGIC_NUMBER_POSITION, len(ROMFS_MAGIC_NUMBER)) == ROMFS_MAGIC_NUMBER:
                print(self.sections[i] + ': ROMFS')
                romfs = RomFs()
                romfs.write_files(folder + os.sep + 'section_' + str(i) + '.files')
            elif read(section_file, KERNEL_MAGIC_NUMBER_POSITION, len(KERNEL_MAGIC_NUMBER)) == KERNEL_MAGIC_NUMBER:
                print(self.sections[i] + ': KERNEL')
                # Nothing
            elif read(section_file, EXT2_MAGIC_NUMBER_POSITION, len(EXT2_MAGIC_NUMBER)) == EXT2_MAGIC_NUMBER:
                print(self.sections[i] + ': EXT2')
                # if (sys.platform == 'linux' or sys.platform == 'linux2') and os.path.exists(folder + os.sep + 'section_' + str(i) + '.ext2'):
                #     print('unmounting ext2')
            elif read(section_file, DTB_MAGIC_NUMBER_POSITION, len(DTB_MAGIC_NUMBER)) == DTB_MAGIC_NUMBER:
                print(self.sections[i] + ': DTB')
                if shutil.which('dtc') is not None and os.path.exists(folder + os.sep + 'section_' + str(i) + '.dts'):
                    print('Packing dts...')
                    dtb_original_size = os.path.getsize(folder + os.sep + 'section_' + str(i) + '.bin')
                    os.system('dtc -q -I dts -O dtb -o - ' + folder + os.sep + 'section_' + str(i) + '.dts' + ' -S ' + str(dtb_original_size) + ' > ' + folder + os.sep + 'section_' + str(i) + '.bin')

            shutil.copyfile(folder + os.sep + 'section_' + str(i) + '.bin', temp_directory + os.sep + 'section_' + str(i) + '.bin')
            shutil.copyfile(folder + os.sep + 'section_' + str(i) + '.header', temp_directory + os.sep + 'section_' + str(i) + '.header')
            section_size = os.path.getsize(temp_directory + os.sep + 'section_' + str(i) + '.bin')
            total_size += section_size + SECTION_HEADER_SIZE
            section_crc32 = calculate_crc32(section_file, 0, section_size)
            section_file.close()
            # Update header CRC32 and size
            header_file = open(temp_directory + os.sep + 'section_' + str(i) + '.header', 'r+b')
            header_file.seek(SECTION_HEADER_CRC32_POSITION)
            header_file.write(section_crc32)
            header_file.seek(SECTION_HEADER_LENGTH_POSITION)
            header_file.write(section_size.to_bytes(SECTION_HEADER_LENGTH_SIZE, 'little'))
            header_file.close()
            # Append header and section to firmware
            header_file = open(temp_directory + os.sep + 'section_' + str(i) + '.header', 'rb')
            section_data_file = open(temp_directory + os.sep + 'section_' + str(i) + '.bin', 'rb')
            section_file = open(temp_directory + os.sep + 'section_' + str(i), 'wb')
            section_file.write(header_file.read())
            section_file.write(section_data_file.read())
            section_file.close()

        # We start with the original firmware header, and later we'll overwrite the CRC32 and the sections data
        print('Creating firmware...')
        shutil.copyfile(folder + os.sep + 'firmware.header', self.firmware_path)
        firmware_file = open(self.firmware_path, 'r+b')
        sections_running_crc32 = bytes(0x0)
        for i in range(0, len(self.sections)):
            print('Adding section {:d} data...'.format(i))
            section_file = open(temp_directory + os.sep + 'section_' + str(i), 'rb')
            firmware_file.seek(0, io.SEEK_END)  # Move to the end to append content
            firmware_file.write(section_file.read())
            print('Updating header info for section {:d}...'.format(i))
            section_size = os.fstat(section_file.fileno()).st_size
            sections_running_crc32 = calculate_crc32(section_file, 0, section_size, int.from_bytes(sections_running_crc32, 'little'))
            sections_running_crc32_inverse = 0xffffffff ^ int.from_bytes(sections_running_crc32, 'little')
            section_crc32 = sections_running_crc32_inverse.to_bytes(FIRMWARE_HEADER_SECTIONS_CRC32_SIZE, 'little')
            firmware_file.seek(FIRMWARE_HEADER_SECTIONS_TABLE_POSITION + (i * FIRMWARE_HEADER_SECTIONS_SIZE))
            if read(section_file, DTB_MAGIC_NUMBER_POSITION + SECTION_HEADER_SIZE, len(DTB_MAGIC_NUMBER)) != DTB_MAGIC_NUMBER:
                firmware_file.write(section_size.to_bytes(FIRMWARE_HEADER_SECTIONS_LENGTH_SIZE, 'little'))
            else:
                firmware_file.write(0x00000000.to_bytes(FIRMWARE_HEADER_SECTIONS_LENGTH_SIZE, 'little'))  # Section 5 (DTB) size is stored always as 0x00000000
            firmware_file.write(section_crc32)
            firmware_file.flush()

        firmware_file.flush()

        print('Adding camera firmware CRC32...')
        firmware_crc32 = calculate_crc32(firmware_file, FIRMWARE_HEADER_SIZE, total_size)
        firmware_file.seek(FIRMWARE_HEADER_CRC32_POSITION)
        firmware_file.write(firmware_crc32)

        firmware_file.flush()

        print('Adding whole firmware MD5...')
        firmware_md5 = calculate_md5(firmware_file, 0, FIRMWARE_HEADER_SIZE + total_size)
        firmware_file.seek(0, io.SEEK_END)
        firmware_file.write(firmware_md5)

        firmware_file.flush()

        # Calculate all camera firmware MD5 for later in the footer
        firmware_footer_size = os.path.getsize(self.firmware_path)
        firmware_footer_md5 = calculate_md5(firmware_file, 0, firmware_footer_size)

        # Add box firmware
        print('Adding box firmware...')
        shutil.copyfile(folder + os.sep + 'box.bin', temp_directory + os.sep + 'box.bin')
        box_file = open(temp_directory + os.sep + 'box.bin', 'rb')
        firmware_file.seek(0, io.SEEK_END)
        firmware_file.write(box_file.read())

        firmware_file.flush()

        # Calculate all box firmware MD5 for later in the footer
        box_footer_size = os.path.getsize(temp_directory + os.sep + 'box.bin')
        box_footer_md5 = calculate_md5(box_file, 0, box_footer_size)

        camera_bluetooth_footer_size = 0
        camera_bluetooth_footer_md5 = None
        box_bluetooth_footer_size = 0
        box_bluetooth_footer_md5 = None
        if self.is_go3:
            # Add camera bluetooth firmware
            print('Adding camera bluetooth firmware...')
            shutil.copyfile(folder + os.sep + 'camera_bt.bin', temp_directory + os.sep + 'camera_bt.bin')
            camera_bluetooth_file = open(temp_directory + os.sep + 'camera_bt.bin', 'rb')
            firmware_file.seek(0, io.SEEK_END)
            firmware_file.write(camera_bluetooth_file.read())

            # Calculate camera bluetooth firmware MD5 for later in the footer
            camera_bluetooth_footer_size = os.path.getsize(temp_directory + os.sep + 'camera_bt.bin')
            camera_bluetooth_footer_md5 = calculate_md5(camera_bluetooth_file, 0, camera_bluetooth_footer_size)

            # Add box bluetooth firmware
            print('Adding box bluetooth firmware...')
            shutil.copyfile(folder + os.sep + 'box_bt.bin', temp_directory + os.sep + 'box_bt.bin')
            box_bluetooth_file = open(temp_directory + os.sep + 'box_bt.bin', 'rb')
            firmware_file.seek(0, io.SEEK_END)
            firmware_file.write(box_bluetooth_file.read())

            # Calculate box bluetooth firmware MD5 for later in the footer
            box_bluetooth_footer_size = os.path.getsize(temp_directory + os.sep + 'box_bt.bin')
            box_bluetooth_footer_md5 = calculate_md5(box_bluetooth_file, 0, box_bluetooth_footer_size)

        # Firmware footer
        print('Adding footer...')
        shutil.copyfile(folder + os.sep + 'firmware.footer', temp_directory + os.sep + 'firmware.footer')
        footer_file = open(temp_directory + os.sep + 'firmware.footer', 'r+b')

        # Set camera firmware size
        footer_file.seek(FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_POSITION)
        footer_file.write(firmware_footer_size.to_bytes(FIRMWARE_FOOTER_CAMERA_FIRMWARE_LENGTH_SIZE, 'little'))

        # Set camera firmware MD5
        footer_file.seek(FIRMWARE_FOOTER_CAMERA_MD5_POSITION)
        footer_file.write(firmware_footer_md5)

        # Set box firmware size
        footer_file.seek(FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_POSITION)
        footer_file.write(box_footer_size.to_bytes(FIRMWARE_FOOTER_BOX_FIRMWARE_LENGTH_SIZE, 'little'))

        # Set box firmware MD5
        footer_file.seek(FIRMWARE_FOOTER_BOX_MD5_POSITION)
        footer_file.write(box_footer_md5)

        if self.is_go3:
            # Set camera bluetooth firmware size
            footer_file.seek(FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FIRMWARE_LENGTH_POSITION)
            footer_file.write(camera_bluetooth_footer_size.to_bytes(FIRMWARE_FOOTER_CAMERA_BLUETOOTH_FIRMWARE_LENGTH_SIZE, 'little'))

            # Set camera bluetooth firmware MD5
            footer_file.seek(FIRMWARE_FOOTER_CAMERA_BLUETOOTH_MD5_POSITION)
            footer_file.write(camera_bluetooth_footer_md5)

            # Set box bluetooth firmware size
            footer_file.seek(FIRMWARE_FOOTER_BOX_BLUETOOTH_FIRMWARE_LENGTH_POSITION)
            footer_file.write(box_bluetooth_footer_size.to_bytes(FIRMWARE_FOOTER_BOX_BLUETOOTH_FIRMWARE_LENGTH_SIZE, 'little'))

            # Set box bluetooth firmware MD5
            footer_file.seek(FIRMWARE_FOOTER_BOX_BLUETOOTH_MD5_POSITION)
            footer_file.write(box_bluetooth_footer_md5)

        footer_file.close()

        footer_file = open(temp_directory + os.sep + 'firmware.footer', 'rb')

        # Append footer
        firmware_file.seek(0, io.SEEK_END)
        firmware_file.write(footer_file.read())

        firmware_file.close()
        footer_file.close()

        shutil.rmtree(temp_directory)

        print('Finished!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='insta360-go-firmware-tool.py',
        description='Insta360 GO 2 and Insta360 GO 3 cameras firmware tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
                Examples:
                $ %(prog)s validate --input=InstaGo2FW.pkg
                $ %(prog)s unpack --input=InstaGo2FW.pkg --output=firmware_folder
                $ %(prog)s pack --input=firmware_folder --output=InstaGo2FW.pkg''')
    )
    parser.add_argument('action', choices=['validate', 'unpack', 'pack'])
    parser.add_argument('-i', '--input', help='Firmware file for validate and unpack actions, folder with the unpacked firmware for pack action')
    parser.add_argument('-o', '--output', help='Folder to unpack the firmware to for unpack action, file to pack to for pack action')

    args = parser.parse_args()
    action = args.action

    if args.input is None:
        print('Input not provided')
        sys.exit(1)
    elif not os.path.exists(args.input):
        print('Input {} does not exist'.format(args.input))
        sys.exit(1)

    if action == 'unpack' or action == 'pack':
        if args.output is None:
            print('Output not provided')
            sys.exit(1)
        elif os.path.exists(args.output):
            print('Output {} already exists'.format(args.output))
            sys.exit(1)

    if action == 'unpack':
        main_firmware_file = args.input
        main_folder = args.output
    elif action == 'pack':
        main_firmware_file = args.output
        main_folder = args.input
    else:
        main_firmware_file = args.input
        main_folder = ''

    firmware = Firmware(main_firmware_file)

    if action == 'unpack':
        firmware.unpack(main_folder)
    elif action == 'pack':
        firmware.pack(main_folder)
    else:
        firmware.validate()

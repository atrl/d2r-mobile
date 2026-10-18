"""Execute generated thunks in Unicorn; no game code is used.
用 Unicorn 执行合成转换片段；不含游戏代码。
"""
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from retarget_apple_guest import thunk, convert, adrp
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn import arm64_const as registers


class RetargetTest(unittest.TestCase):
    def test_every_destination_preserves_machine_state(self):
        for destination in range(31):
            with self.subTest(destination=destination):
                machine = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
                machine.mem_map(0x100000, 0x20000)
                machine.mem_map(0x200000, 0x10000)
                machine.mem_write(0x104000, thunk(0x104000, 0x100100, destination, 0x108000))
                machine.mem_write(0x108040, struct.pack('<Q', 0x110000))
                # Context entry contract: only x16 changes, as in generate_entry.py.
                machine.mem_write(0x110000, struct.pack('<II', 0xd2800010 | (0x7000 << 5), 0xd65f03c0))
                original = [0x123456780000 + index for index in range(31)]
                for index, value in enumerate(original):
                    machine.reg_write(getattr(registers, 'UC_ARM64_REG_X' + str(index)), value)
                sp = 0x208000
                machine.reg_write(registers.UC_ARM64_REG_SP, sp)
                machine.reg_write(registers.UC_ARM64_REG_NZCV, 0xa0000000)
                redzone = bytes(range(128))
                machine.mem_write(sp - 128, redzone)
                machine.emu_start(0x104000, 0x100100, count=30)
                self.assertEqual(machine.reg_read(registers.UC_ARM64_REG_PC), 0x100100)
                for index, value in enumerate(original):
                    self.assertEqual(machine.reg_read(getattr(registers, 'UC_ARM64_REG_X' + str(index))),
                                     0x7000 if index == destination else value)
                self.assertEqual(machine.reg_read(registers.UC_ARM64_REG_SP), sp)
                self.assertEqual(machine.reg_read(registers.UC_ARM64_REG_NZCV), 0xa0000000)
                self.assertEqual(bytes(machine.mem_read(sp - 128, 128)), redzone)

    def test_conversion_checks_pattern_and_preserves_addresses(self):
        layout = {'TEXT_END': 0x1000, 'KEY_PAGE_OFF': 0x4000, 'PATCH_OFF': 0x8000}
        for index, name in enumerate(('K18','KTLS','KTLR','KGATE','KRES0','KRES1','KASPECT','KASPECTUI')):
            layout['KEY_' + name + '_IDX'] = index
        data = bytearray(0xc000)
        struct.pack_into('<4I', data, 0x8000, 0xd53bd070, adrp(17, 0x8004, 0x4000), 0xf9400231, 0x8b110210)
        result, count = convert(data, layout)
        self.assertEqual(count, 1)
        self.assertEqual(len(result), len(data) + 40)
        self.assertEqual(result[:0x8000], data[:0x8000])
        self.assertEqual(result[0x8004:len(data)], data[0x8004:])
        data[0x800c] ^= 1
        with self.assertRaisesRegex(ValueError, 'unrecognized'):
            convert(data, layout)


if __name__ == '__main__': unittest.main()

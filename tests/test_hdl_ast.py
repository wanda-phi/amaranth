# amaranth: UnusedPrint=no, UnusedProperty=no

import warnings
from enum import Enum, EnumMeta

from amaranth.hdl._ast import *
from amaranth.lib.enum import Enum as AmaranthEnum

from .utils import *
from amaranth._utils import _ignore_deprecated


class UnsignedEnum(Enum):
    FOO = 1
    BAR = 2
    BAZ = 3


class SignedEnum(Enum):
    FOO = -1
    BAR =  0
    BAZ = +1


class StringEnum(Enum):
    FOO = "a"
    BAR = "b"


class TypedEnum(int, Enum):
    FOO = 1
    BAR = 2
    BAZ = 3


class ShapeTestCase(FHDLTestCase):
    def test_make(self):
        s1 = Shape()
        self.assertEqual(s1.width, 1)
        self.assertEqual(s1.signed, False)
        s2 = Shape(signed=True)
        self.assertEqual(s2.width, 1)
        self.assertEqual(s2.signed, True)
        s3 = Shape(3, True)
        self.assertEqual(s3.width, 3)
        self.assertEqual(s3.signed, True)
        s4 = Shape(0)
        self.assertEqual(s4.width, 0)
        self.assertEqual(s4.signed, False)

    def test_make_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Width must be an integer, not 'a'$"):
            Shape("a")
        with self.assertRaisesRegex(TypeError,
                r"^Width of an unsigned value must be zero or a positive integer, not -1$"):
            Shape(-1, signed=False)
        with self.assertRaisesRegex(TypeError,
                r"^Width of a signed value must be a positive integer, not 0$"):
            Shape(0, signed=True)

    def test_compare_non_shape(self):
        self.assertNotEqual(Shape(1, True), "hi")

    def test_repr(self):
        self.assertEqual(repr(Shape()), "unsigned(1)")
        self.assertEqual(repr(Shape(2, True)), "signed(2)")

    def test_convert_tuple_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^cannot unpack non-iterable Shape object$"):
            width, signed = Shape()

    def test_unsigned(self):
        s1 = unsigned(2)
        self.assertIsInstance(s1, Shape)
        self.assertEqual(s1.width, 2)
        self.assertEqual(s1.signed, False)

    def test_signed(self):
        s1 = signed(2)
        self.assertIsInstance(s1, Shape)
        self.assertEqual(s1.width, 2)
        self.assertEqual(s1.signed, True)

    def test_cast_shape(self):
        s1 = Shape.cast(unsigned(1))
        self.assertEqual(s1.width, 1)
        self.assertEqual(s1.signed, False)
        s2 = Shape.cast(signed(3))
        self.assertEqual(s2.width, 3)
        self.assertEqual(s2.signed, True)

    def test_cast_int(self):
        s1 = Shape.cast(2)
        self.assertEqual(s1.width, 2)
        self.assertEqual(s1.signed, False)

    def test_cast_int_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Width of an unsigned value must be zero or a positive integer, not -1$"):
            Shape.cast(-1)

    def test_cast_tuple_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Object \(1, True\) cannot be converted to an Amaranth shape$"):
            Shape.cast((1, True))

    def test_cast_range(self):
        s1 = Shape.cast(range(0, 8))
        self.assertEqual(s1.width, 3)
        self.assertEqual(s1.signed, False)
        s2 = Shape.cast(range(0, 9))
        self.assertEqual(s2.width, 4)
        self.assertEqual(s2.signed, False)
        s3 = Shape.cast(range(-7, 8))
        self.assertEqual(s3.width, 4)
        self.assertEqual(s3.signed, True)
        s4 = Shape.cast(range(0, 1))
        self.assertEqual(s4.width, 0)
        self.assertEqual(s4.signed, False)
        s5 = Shape.cast(range(-1, 0))
        self.assertEqual(s5.width, 1)
        self.assertEqual(s5.signed, True)
        s6 = Shape.cast(range(0, 0))
        self.assertEqual(s6.width, 0)
        self.assertEqual(s6.signed, False)
        s7 = Shape.cast(range(-1, -1))
        self.assertEqual(s7.width, 0)
        self.assertEqual(s7.signed, False)
        s8 = Shape.cast(range(0, 10, 3))
        self.assertEqual(s8.width, 4)
        self.assertEqual(s8.signed, False)
        s9 = Shape.cast(range(0, 3, 3))
        self.assertEqual(s9.width, 0)
        self.assertEqual(s9.signed, False)

    def test_cast_enum(self):
        s1 = Shape.cast(UnsignedEnum)
        self.assertEqual(s1.width, 2)
        self.assertEqual(s1.signed, False)
        s2 = Shape.cast(SignedEnum)
        self.assertEqual(s2.width, 2)
        self.assertEqual(s2.signed, True)

    def test_cast_enum_bad(self):
        with self.assertRaisesRegex(TypeError,
                r"^Only enumerations whose members have constant-castable values can be used "
                r"in Amaranth code$"):
            Shape.cast(StringEnum)

    def test_cast_bad(self):
        with self.assertRaisesRegex(TypeError,
                r"^Object 'foo' cannot be converted to an Amaranth shape$"):
            Shape.cast("foo")

    def test_hashable(self):
        d = {
            signed(2): "a",
            unsigned(3): "b",
            unsigned(2): "c",
        }
        self.assertEqual(d[signed(2)], "a")
        self.assertEqual(d[unsigned(3)], "b")
        self.assertEqual(d[unsigned(2)], "c")


class MockShapeCastable(ShapeCastable):
    def __init__(self, dest):
        self.dest = dest

    def as_shape(self):
        return self.dest

    def __call__(self, value):
        return value

    def const(self, init):
        return Const(init, self.dest)

    def from_bits(self, bits):
        return bits


class ShapeCastableTestCase(FHDLTestCase):
    def test_no_override(self):
        with self.assertRaisesRegex(TypeError,
                r"^Class '.+\.MockShapeCastableNoOverride' deriving from 'ShapeCastable' must "
                r"override the 'as_shape' method$"):
            class MockShapeCastableNoOverride(ShapeCastable):
                def __init__(self):
                    pass

    def test_cast(self):
        sc = MockShapeCastable(unsigned(2))
        self.assertEqual(Shape.cast(sc), unsigned(2))

    def test_recurse_bad(self):
        sc = MockShapeCastable(None)
        sc.dest = sc
        with self.assertRaisesRegex(RecursionError,
                r"^Shape-castable object <.+> casts to itself$"):
            Shape.cast(sc)

    def test_recurse(self):
        sc = MockShapeCastable(MockShapeCastable(unsigned(1)))
        self.assertEqual(Shape.cast(sc), unsigned(1))

    def test_abstract(self):
        with self.assertRaisesRegex(TypeError,
                r"^Can't instantiate abstract class ShapeCastable$"):
            ShapeCastable()


class ShapeLikeTestCase(FHDLTestCase):
    def test_construct(self):
        with self.assertRaises(TypeError):
            ShapeLike()

    def test_subclass(self):
        self.assertTrue(issubclass(Shape, ShapeLike))
        self.assertTrue(issubclass(MockShapeCastable, ShapeLike))
        self.assertTrue(issubclass(int, ShapeLike))
        self.assertTrue(issubclass(range, ShapeLike))
        self.assertTrue(issubclass(EnumMeta, ShapeLike))
        self.assertFalse(issubclass(Enum, ShapeLike))
        self.assertFalse(issubclass(str, ShapeLike))
        self.assertTrue(issubclass(ShapeLike, ShapeLike))

    def test_isinstance(self):
        self.assertTrue(isinstance(unsigned(2), ShapeLike))
        self.assertTrue(isinstance(MockShapeCastable(unsigned(2)), ShapeLike))
        self.assertTrue(isinstance(2, ShapeLike))
        self.assertTrue(isinstance(0, ShapeLike))
        self.assertFalse(isinstance(-1, ShapeLike))
        self.assertTrue(isinstance(range(10), ShapeLike))
        self.assertFalse(isinstance("abc", ShapeLike))

    def test_isinstance_enum(self):
        class EnumA(Enum):
            A = 1
            B = 2
        class EnumB(Enum):
            A = "a"
            B = "b"
        class EnumC(Enum):
            A = Cat(Const(1, 2), Const(0, 2))
        self.assertTrue(isinstance(EnumA, ShapeLike))
        self.assertFalse(isinstance(EnumB, ShapeLike))
        self.assertTrue(isinstance(EnumC, ShapeLike))


class ValueTestCase(FHDLTestCase):
    def test_cast(self):
        self.assertIsInstance(Value.cast(0), Const)
        self.assertIsInstance(Value.cast(True), Const)
        c = Const(0)
        self.assertIs(Value.cast(c), c)
        with self.assertRaisesRegex(TypeError,
                r"^Object 'str' cannot be converted to an Amaranth value$"):
            Value.cast("str")

    def test_cast_enum(self):
        e1 = Value.cast(UnsignedEnum.FOO)
        self.assertIsInstance(e1, Const)
        self.assertEqual(e1.shape(), unsigned(2))
        e2 = Value.cast(SignedEnum.FOO)
        self.assertIsInstance(e2, Const)
        self.assertEqual(e2.shape(), signed(2))

    def test_cast_typedenum(self):
        e1 = Value.cast(TypedEnum.FOO)
        self.assertIsInstance(e1, Const)
        self.assertEqual(e1.shape(), unsigned(2))

    def test_cast_enum_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Only enumerations whose members have constant-castable values can be used "
                r"in Amaranth code$"):
            Value.cast(StringEnum.FOO)

    def test_bool(self):
        with self.assertRaisesRegex(TypeError,
                r"^Attempted to convert Amaranth value to Python boolean$"):
            if Const(0):
                pass

    def test_len(self):
        self.assertEqual(len(Const(10)), 4)

    def test_getitem_int(self):
        s1 = Const(10)[0]
        self.assertIsInstance(s1, Slice)
        self.assertEqual(s1.start, 0)
        self.assertEqual(s1.stop, 1)
        s2 = Const(10)[-1]
        self.assertIsInstance(s2, Slice)
        self.assertEqual(s2.start, 3)
        self.assertEqual(s2.stop, 4)
        with self.assertRaisesRegex(IndexError,
                r"^Index 5 is out of bounds for a 4-bit value$"):
            Const(10)[5]

    def test_getitem_slice(self):
        s1 = Const(10)[1:3]
        self.assertIsInstance(s1, Slice)
        self.assertEqual(s1.start, 1)
        self.assertEqual(s1.stop, 3)
        s2 = Const(10)[1:-2]
        self.assertIsInstance(s2, Slice)
        self.assertEqual(s2.start, 1)
        self.assertEqual(s2.stop, 2)
        s3 = Const(31)[::2]
        self.assertIsInstance(s3, Concat)
        self.assertIsInstance(s3.parts[0], Slice)
        self.assertEqual(s3.parts[0].start, 0)
        self.assertEqual(s3.parts[0].stop, 1)
        self.assertIsInstance(s3.parts[1], Slice)
        self.assertEqual(s3.parts[1].start, 2)
        self.assertEqual(s3.parts[1].stop, 3)
        self.assertIsInstance(s3.parts[2], Slice)
        self.assertEqual(s3.parts[2].start, 4)
        self.assertEqual(s3.parts[2].stop, 5)

    def test_getitem_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Cannot index value with 'str'$"):
            Const(31)["str"]
        with self.assertRaisesRegex(TypeError,
                r"^Cannot index value with a value; use Value.bit_select\(\) instead$"):
            Const(31)[Signal(3)]
        s = Signal(3)
        with self.assertRaisesRegex(TypeError,
                r"^Cannot slice value with a value; use Value.bit_select\(\) or Value.word_select\(\) instead$"):
            Const(31)[s:s+3]

    def test_shift_left(self):
        self.assertRepr(Const(256, unsigned(9)).shift_left(0),
                        "(cat (const 0'd0) (const 9'd256))")

        self.assertRepr(Const(256, unsigned(9)).shift_left(1),
                        "(cat (const 1'd0) (const 9'd256))")
        self.assertRepr(Const(256, unsigned(9)).shift_left(5),
                        "(cat (const 5'd0) (const 9'd256))")
        self.assertRepr(Const(256, signed(9)).shift_left(1),
                        "(s (cat (const 1'd0) (const 9'sd-256)))")
        self.assertRepr(Const(256, signed(9)).shift_left(5),
                        "(s (cat (const 5'd0) (const 9'sd-256)))")

        self.assertRepr(Const(256, unsigned(9)).shift_left(-1),
                        "(slice (const 9'd256) 1:9)")
        self.assertRepr(Const(256, unsigned(9)).shift_left(-5),
                        "(slice (const 9'd256) 5:9)")
        self.assertRepr(Const(256, signed(9)).shift_left(-1),
                        "(s (slice (const 9'sd-256) 1:9))")
        self.assertRepr(Const(256, signed(9)).shift_left(-5),
                        "(s (slice (const 9'sd-256) 5:9))")
        self.assertRepr(Const(256, signed(9)).shift_left(-15),
                        "(s (slice (const 9'sd-256) 8:9))")

    def test_shift_left_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Shift amount must be an integer, not 'str'$"):
            Const(31).shift_left("str")

    def test_shift_right(self):
        self.assertRepr(Const(256, unsigned(9)).shift_right(0),
                        "(slice (const 9'd256) 0:9)")

        self.assertRepr(Const(256, unsigned(9)).shift_right(-1),
                        "(cat (const 1'd0) (const 9'd256))")
        self.assertRepr(Const(256, unsigned(9)).shift_right(-5),
                        "(cat (const 5'd0) (const 9'd256))")
        self.assertRepr(Const(256, signed(9)).shift_right(-1),
                        "(s (cat (const 1'd0) (const 9'sd-256)))")
        self.assertRepr(Const(256, signed(9)).shift_right(-5),
                        "(s (cat (const 5'd0) (const 9'sd-256)))")

        self.assertRepr(Const(256, unsigned(9)).shift_right(1),
                        "(slice (const 9'd256) 1:9)")
        self.assertRepr(Const(256, unsigned(9)).shift_right(5),
                        "(slice (const 9'd256) 5:9)")
        self.assertRepr(Const(256, unsigned(9)).shift_right(15),
                        "(slice (const 9'd256) 9:9)")
        self.assertRepr(Const(256, signed(9)).shift_right(1),
                        "(s (slice (const 9'sd-256) 1:9))")
        self.assertRepr(Const(256, signed(9)).shift_right(5),
                        "(s (slice (const 9'sd-256) 5:9))")
        self.assertRepr(Const(256, signed(9)).shift_right(7),
                        "(s (slice (const 9'sd-256) 7:9))")
        self.assertRepr(Const(256, signed(9)).shift_right(8),
                        "(s (slice (const 9'sd-256) 8:9))")
        self.assertRepr(Const(256, signed(9)).shift_right(9),
                        "(s (slice (const 9'sd-256) 8:9))")
        self.assertRepr(Const(256, signed(9)).shift_right(15),
                        "(s (slice (const 9'sd-256) 8:9))")

    def test_shift_right_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Shift amount must be an integer, not 'str'$"):
            Const(31).shift_left("str")

    def test_rotate_left(self):
        self.assertRepr(Const(256).rotate_left(1),
                        "(cat (slice (const 9'd256) 8:9) (slice (const 9'd256) 0:8))")
        self.assertRepr(Const(256).rotate_left(7),
                        "(cat (slice (const 9'd256) 2:9) (slice (const 9'd256) 0:2))")
        self.assertRepr(Const(256).rotate_left(-1),
                        "(cat (slice (const 9'd256) 1:9) (slice (const 9'd256) 0:1))")
        self.assertRepr(Const(256).rotate_left(-7),
                        "(cat (slice (const 9'd256) 7:9) (slice (const 9'd256) 0:7))")
        self.assertRepr(Const(0, 0).rotate_left(3),
                        "(cat (slice (const 0'd0) 0:0) (slice (const 0'd0) 0:0))")
        self.assertRepr(Const(0, 0).rotate_left(-3),
                        "(cat (slice (const 0'd0) 0:0) (slice (const 0'd0) 0:0))")

    def test_rotate_left_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Rotate amount must be an integer, not 'str'$"):
            Const(31).rotate_left("str")

    def test_rotate_right(self):
        self.assertRepr(Const(256).rotate_right(1),
                        "(cat (slice (const 9'd256) 1:9) (slice (const 9'd256) 0:1))")
        self.assertRepr(Const(256).rotate_right(7),
                        "(cat (slice (const 9'd256) 7:9) (slice (const 9'd256) 0:7))")
        self.assertRepr(Const(256).rotate_right(-1),
                        "(cat (slice (const 9'd256) 8:9) (slice (const 9'd256) 0:8))")
        self.assertRepr(Const(256).rotate_right(-7),
                        "(cat (slice (const 9'd256) 2:9) (slice (const 9'd256) 0:2))")
        self.assertRepr(Const(0, 0).rotate_right(3),
                        "(cat (slice (const 0'd0) 0:0) (slice (const 0'd0) 0:0))")
        self.assertRepr(Const(0, 0).rotate_right(-3),
                        "(cat (slice (const 0'd0) 0:0) (slice (const 0'd0) 0:0))")

    def test_rotate_right_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Rotate amount must be an integer, not 'str'$"):
            Const(31).rotate_right("str")

    def test_replicate_shape(self):
        s1 = Const(10).replicate(3)
        self.assertEqual(s1.shape(), unsigned(12))
        self.assertIsInstance(s1.shape(), Shape)
        s2 = Const(10).replicate(0)
        self.assertEqual(s2.shape(), unsigned(0))

    def test_replicate_count_wrong(self):
        with self.assertRaises(TypeError):
            Const(10).replicate(-1)
        with self.assertRaises(TypeError):
            Const(10).replicate("str")

    def test_replicate_repr(self):
        s = Const(10).replicate(3)
        self.assertEqual(repr(s), "(cat (const 4'd10) (const 4'd10) (const 4'd10))")

    def test_format_wrong(self):
        sig = Signal()
        with self.assertRaisesRegex(TypeError,
                r"^Value \(sig sig\) cannot be converted to string."):
            f"{sig}"


class ConstTestCase(FHDLTestCase):
    def test_shape(self):
        self.assertEqual(Const(0).shape(),   unsigned(1))
        self.assertIsInstance(Const(0).shape(), Shape)
        self.assertEqual(Const(1).shape(),   unsigned(1))
        self.assertEqual(Const(10).shape(),  unsigned(4))
        self.assertEqual(Const(-10).shape(), signed(5))

        self.assertEqual(Const(1, 4).shape(),          unsigned(4))
        self.assertEqual(Const(-1, 4).shape(),         signed(4))
        self.assertEqual(Const(1, signed(4)).shape(),  signed(4))
        self.assertEqual(Const(0, unsigned(0)).shape(), unsigned(0))

    def test_shape_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Width of an unsigned value must be zero or a positive integer, not -1$"):
            Const(1, -1)

    def test_wrong_fencepost(self):
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Value 10 equals the non-inclusive end of the constant shape "
                r"range\(0, 10\); this is likely an off-by-one error$"):
            Const(10, range(10))

    def test_normalization(self):
        self.assertEqual(Const(0b10110, signed(5)).value, -10)
        self.assertEqual(Const(0b10000, signed(4)).value, 0)
        self.assertEqual(Const(-16, 4).value, 0)

    def test_value(self):
        self.assertEqual(Const(10).value, 10)

    def test_repr(self):
        self.assertEqual(repr(Const(10)),  "(const 4'd10)")
        self.assertEqual(repr(Const(-10)), "(const 5'sd-10)")

    def test_hash(self):
        with self.assertRaises(TypeError):
            hash(Const(0))

    def test_enum(self):
        e1 = Const(UnsignedEnum.FOO)
        self.assertIsInstance(e1, Const)
        self.assertEqual(e1.shape(), unsigned(2))
        e2 = Const(SignedEnum.FOO)
        self.assertIsInstance(e2, Const)
        self.assertEqual(e2.shape(), signed(2))
        e3 = Const(TypedEnum.FOO)
        self.assertIsInstance(e3, Const)
        self.assertEqual(e3.shape(), unsigned(2))
        e4 = Const(UnsignedEnum.FOO, 4)
        self.assertIsInstance(e4, Const)
        self.assertEqual(e4.shape(), unsigned(4))

    def test_shape_castable(self):
        class MockConstValue(ValueCastable):
            def __init__(self, value):
                self.value = value

            def shape(self):
                return MockConstShape()

            def as_value(self):
                return Const(self.value, 8)

        class MockConstShape(ShapeCastable):
            def as_shape(self):
                return unsigned(8)

            def __call__(self, value):
                return value

            def const(self, init):
                return MockConstValue(init)

            def from_bits(self, bits):
                return bits

        s = Const(10, MockConstShape())
        self.assertIsInstance(s, MockConstValue)
        self.assertEqual(s.value, 10)


class OperatorTestCase(FHDLTestCase):
    def test_bool(self):
        v = Const(0, 4).bool()
        self.assertEqual(repr(v), "(b (const 4'd0))")
        self.assertEqual(v.shape(), unsigned(1))

    def test_invert(self):
        v = ~Const(0, 4)
        self.assertEqual(repr(v), "(~ (const 4'd0))")
        self.assertEqual(v.shape(), unsigned(4))

    def test_as_unsigned(self):
        v = Const(-1, signed(4)).as_unsigned()
        self.assertEqual(repr(v), "(u (const 4'sd-1))")
        self.assertEqual(v.shape(), unsigned(4))

    def test_as_signed(self):
        v = Const(1, unsigned(4)).as_signed()
        self.assertEqual(repr(v), "(s (const 4'd1))")
        self.assertEqual(v.shape(), signed(4))

    def test_as_signed_wrong(self):
        with self.assertRaisesRegex(ValueError,
                r"^Cannot create a 0-width signed value$"):
            Const(0, 0).as_signed()

    def test_pos(self):
        self.assertRepr(+Const(10), "(const 4'd10)")

    def test_neg(self):
        v1 = -Const(0, unsigned(4))
        self.assertEqual(repr(v1), "(- (const 4'd0))")
        self.assertEqual(v1.shape(), signed(5))
        v2 = -Const(0, signed(4))
        self.assertEqual(repr(v2), "(- (const 4'sd0))")
        self.assertEqual(v2.shape(), signed(5))

    def test_add(self):
        v1 = Const(0, unsigned(4)) + Const(0, unsigned(6))
        self.assertEqual(repr(v1), "(+ (const 4'd0) (const 6'd0))")
        self.assertEqual(v1.shape(), unsigned(7))
        v2 = Const(0, signed(4)) + Const(0, signed(6))
        self.assertEqual(v2.shape(), signed(7))
        v3 = Const(0, signed(4)) + Const(0, unsigned(4))
        self.assertEqual(v3.shape(), signed(6))
        v4 = Const(0, unsigned(4)) + Const(0, signed(4))
        self.assertEqual(v4.shape(), signed(6))
        v5 = 10 + Const(0, 4)
        self.assertEqual(v5.shape(), unsigned(5))

    def test_sub(self):
        v1 = Const(0, unsigned(4)) - Const(0, unsigned(6))
        self.assertEqual(repr(v1), "(- (const 4'd0) (const 6'd0))")
        self.assertEqual(v1.shape(), signed(7))
        v2 = Const(0, signed(4)) - Const(0, signed(6))
        self.assertEqual(v2.shape(), signed(7))
        v3 = Const(0, signed(4)) - Const(0, unsigned(4))
        self.assertEqual(v3.shape(), signed(6))
        v4 = Const(0, unsigned(4)) - Const(0, signed(4))
        self.assertEqual(v4.shape(), signed(6))
        v5 = 10 - Const(0, 4)
        self.assertEqual(v5.shape(), signed(5))
        v6 = 1 - Const(2)
        self.assertEqual(v6.shape(), signed(3))

    def test_mul(self):
        v1 = Const(0, unsigned(4)) * Const(0, unsigned(6))
        self.assertEqual(repr(v1), "(* (const 4'd0) (const 6'd0))")
        self.assertEqual(v1.shape(), unsigned(10))
        v2 = Const(0, signed(4)) * Const(0, signed(6))
        self.assertEqual(v2.shape(), signed(10))
        v3 = Const(0, signed(4)) * Const(0, unsigned(4))
        self.assertEqual(v3.shape(), signed(8))
        v5 = 10 * Const(0, 4)
        self.assertEqual(v5.shape(), unsigned(8))

    def test_mod(self):
        v1 = Const(0, unsigned(4)) % Const(0, unsigned(6))
        self.assertEqual(repr(v1), "(% (const 4'd0) (const 6'd0))")
        self.assertEqual(v1.shape(), unsigned(6))
        v3 = Const(0, signed(4)) % Const(0, unsigned(4))
        self.assertEqual(v3.shape(), unsigned(4))
        v4 = Const(0, signed(4)) % Const(0, signed(6))
        self.assertEqual(v4.shape(), signed(6))
        v5 = 10 % Const(0, 4)
        self.assertEqual(v5.shape(), unsigned(4))

    def test_floordiv(self):
        v1 = Const(0, unsigned(4)) // Const(0, unsigned(6))
        self.assertEqual(repr(v1), "(// (const 4'd0) (const 6'd0))")
        self.assertEqual(v1.shape(), unsigned(4))
        v3 = Const(0, signed(4)) // Const(0, unsigned(4))
        self.assertEqual(v3.shape(), signed(4))
        v4 = Const(0, signed(4)) // Const(0, signed(6))
        self.assertEqual(v4.shape(), signed(5))
        v5 = 10 // Const(0, 4)
        self.assertEqual(v5.shape(), unsigned(4))

    def test_and(self):
        v1 = Const(0, unsigned(4)) & Const(0, unsigned(6))
        self.assertEqual(repr(v1), "(& (const 4'd0) (const 6'd0))")
        self.assertEqual(v1.shape(), unsigned(6))
        v2 = Const(0, signed(4)) & Const(0, signed(6))
        self.assertEqual(v2.shape(), signed(6))
        v3 = Const(0, signed(4)) & Const(0, unsigned(4))
        self.assertEqual(v3.shape(), signed(5))
        v4 = Const(0, unsigned(4)) & Const(0, signed(4))
        self.assertEqual(v4.shape(), signed(5))
        v5 = 10 & Const(0, 4)
        self.assertEqual(v5.shape(), unsigned(4))

    def test_or(self):
        v1 = Const(0, unsigned(4)) | Const(0, unsigned(6))
        self.assertEqual(repr(v1), "(| (const 4'd0) (const 6'd0))")
        self.assertEqual(v1.shape(), unsigned(6))
        v2 = Const(0, signed(4)) | Const(0, signed(6))
        self.assertEqual(v2.shape(), signed(6))
        v3 = Const(0, signed(4)) | Const(0, unsigned(4))
        self.assertEqual(v3.shape(), signed(5))
        v4 = Const(0, unsigned(4)) | Const(0, signed(4))
        self.assertEqual(v4.shape(), signed(5))
        v5 = 10 | Const(0, 4)
        self.assertEqual(v5.shape(), unsigned(4))

    def test_xor(self):
        v1 = Const(0, unsigned(4)) ^ Const(0, unsigned(6))
        self.assertEqual(repr(v1), "(^ (const 4'd0) (const 6'd0))")
        self.assertEqual(v1.shape(), unsigned(6))
        v2 = Const(0, signed(4)) ^ Const(0, signed(6))
        self.assertEqual(v2.shape(), signed(6))
        v3 = Const(0, signed(4)) ^ Const(0, unsigned(4))
        self.assertEqual(v3.shape(), signed(5))
        v4 = Const(0, unsigned(4)) ^ Const(0, signed(4))
        self.assertEqual(v4.shape(), signed(5))
        v5 = 10 ^ Const(0, 4)
        self.assertEqual(v5.shape(), unsigned(4))

    def test_shl(self):
        v1 = Const(1, 4) << Const(4)
        self.assertEqual(repr(v1), "(<< (const 4'd1) (const 3'd4))")
        self.assertEqual(v1.shape(), unsigned(11))

    def test_shl_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Shift amount must be unsigned$"):
            1 << Const(0, signed(6))
        with self.assertRaisesRegex(TypeError,
                r"^Shift amount must be unsigned$"):
            Const(1, unsigned(4)) << -1

    def test_shr(self):
        v1 = Const(1, 4) >> Const(4)
        self.assertEqual(repr(v1), "(>> (const 4'd1) (const 3'd4))")
        self.assertEqual(v1.shape(), unsigned(4))

    def test_shr_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Shift amount must be unsigned$"):
            1 << Const(0, signed(6))
        with self.assertRaisesRegex(TypeError,
                r"^Shift amount must be unsigned$"):
            Const(1, unsigned(4)) << -1

    def test_lt(self):
        v = Const(0, 4) < Const(0, 6)
        self.assertEqual(repr(v), "(< (const 4'd0) (const 6'd0))")
        self.assertEqual(v.shape(), unsigned(1))

    def test_le(self):
        v = Const(0, 4) <= Const(0, 6)
        self.assertEqual(repr(v), "(<= (const 4'd0) (const 6'd0))")
        self.assertEqual(v.shape(), unsigned(1))

    def test_gt(self):
        v = Const(0, 4) > Const(0, 6)
        self.assertEqual(repr(v), "(> (const 4'd0) (const 6'd0))")
        self.assertEqual(v.shape(), unsigned(1))

    def test_ge(self):
        v = Const(0, 4) >= Const(0, 6)
        self.assertEqual(repr(v), "(>= (const 4'd0) (const 6'd0))")
        self.assertEqual(v.shape(), unsigned(1))

    def test_eq(self):
        v = Const(0, 4) == Const(0, 6)
        self.assertEqual(repr(v), "(== (const 4'd0) (const 6'd0))")
        self.assertEqual(v.shape(), unsigned(1))

    def test_ne(self):
        v = Const(0, 4) != Const(0, 6)
        self.assertEqual(repr(v), "(!= (const 4'd0) (const 6'd0))")
        self.assertEqual(v.shape(), unsigned(1))

    def test_mux(self):
        s  = Const(0)
        v1 = Mux(s, Const(0, unsigned(4)), Const(0, unsigned(6)))
        self.assertEqual(repr(v1), "(switch-value (const 1'd0) (case 0 (const 6'd0)) (default (const 4'd0)))")
        self.assertEqual(v1.shape(), unsigned(6))
        v2 = Mux(s, Const(0, signed(4)), Const(0, signed(6)))
        self.assertEqual(v2.shape(), signed(6))
        v3 = Mux(s, Const(0, signed(4)), Const(0, unsigned(4)))
        self.assertEqual(v3.shape(), signed(5))
        v4 = Mux(s, Const(0, unsigned(4)), Const(0, signed(4)))
        self.assertEqual(v4.shape(), signed(5))

    def test_mux_wide(self):
        s = Const(0b100)
        v = Mux(s, Const(0, unsigned(4)), Const(0, unsigned(6)))
        self.assertEqual(repr(v), "(switch-value (const 3'd4) (case 000 (const 6'd0)) (default (const 4'd0)))")

    def test_mux_bool(self):
        v = Mux(True, Const(0), Const(0))
        self.assertEqual(repr(v), "(switch-value (const 1'd1) (case 0 (const 1'd0)) (default (const 1'd0)))")

    def test_any(self):
        v = Const(0b101).any()
        self.assertEqual(repr(v), "(r| (const 3'd5))")

    def test_all(self):
        v = Const(0b101).all()
        self.assertEqual(repr(v), "(r& (const 3'd5))")

    def test_xor_value(self):
        v = Const(0b101).xor()
        self.assertEqual(repr(v), "(r^ (const 3'd5))")

    def test_matches(self):
        s = Signal(4)
        self.assertRepr(s.matches(), "(const 1'd0)")
        self.assertRepr(s.matches(1), """
        (== (sig s) (const 1'd1))
        """)
        self.assertRepr(s.matches(0, 1), """
        (r| (cat (== (sig s) (const 1'd0)) (== (sig s) (const 1'd1))))
        """)
        self.assertRepr(s.matches("10--"), """
        (== (& (sig s) (const 4'd12)) (const 4'd8))
        """)
        self.assertRepr(s.matches("1 0--"), """
        (== (& (sig s) (const 4'd12)) (const 4'd8))
        """)

    def test_matches_enum(self):
        s = Signal(SignedEnum)
        self.assertRepr(s.matches(SignedEnum.FOO), """
        (== (sig s) (const 1'sd-1))
        """)

    def test_matches_const_castable(self):
        s = Signal(4)
        self.assertRepr(s.matches(Cat(C(0b10, 2), C(0b11, 2))), """
        (== (sig s) (const 4'd14))
        """)

    def test_matches_width_wrong(self):
        s = Signal(4)
        with self.assertRaisesRegex(SyntaxError,
                r"^Pattern '--' must have the same width as match value \(which is 4\)$"):
            s.matches("--")
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Pattern '22' \(5'10110\) is not representable in match value shape "
                r"\(unsigned\(4\)\); comparison will never be true$"):
            s.matches(0b10110)
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Pattern '\(cat \(const 1'd0\) \(const 4'd11\)\)' \(5'10110\) is not "
                r"representable in match value shape \(unsigned\(4\)\); comparison will never be true$"):
            s.matches(Cat(0, C(0b1011, 4)))

    def test_matches_bits_wrong(self):
        s = Signal(4)
        with self.assertRaisesRegex(SyntaxError,
                r"^Pattern 'abc' must consist of 0, 1, and - \(don't care\) bits, "
                r"and may include whitespace$"):
            s.matches("abc")

    def test_matches_pattern_wrong(self):
        s = Signal(4)
        with self.assertRaisesRegex(SyntaxError,
                r"^Pattern must be a string or a constant-castable expression, not 1\.0$"):
            s.matches(1.0)

    def test_hash(self):
        with self.assertRaises(TypeError):
            hash(Const(0) + Const(0))

    def test_abs(self):
        s = Signal(4)
        self.assertRepr(abs(s), """
        (sig s)
        """)
        s = Signal(signed(4))
        self.assertRepr(abs(s), """
        (slice (switch-value (>= (sig s) (const 1'd0)) (case 0 (- (sig s))) (default (sig s))) 0:4)
        """)
        self.assertEqual(abs(s).shape(), unsigned(4))

    def test_contains(self):
        with self.assertRaisesRegex(TypeError,
                r"^Cannot use 'in' with an Amaranth value$"):
            1 in Signal(3)


class SliceTestCase(FHDLTestCase):
    def test_shape(self):
        s1 = Const(10)[2]
        self.assertEqual(s1.shape(), unsigned(1))
        self.assertIsInstance(s1.shape(), Shape)
        s2 = Const(-10)[0:2]
        self.assertEqual(s2.shape(), unsigned(2))

    def test_start_end_negative(self):
        c  = Const(0, 8)
        s1 = Slice(c, 0, -1)
        self.assertEqual((s1.start, s1.stop), (0, 7))
        s1 = Slice(c, -4, -1)
        self.assertEqual((s1.start, s1.stop), (4, 7))

    def test_start_end_bool(self):
        c  = Const(0, 8)
        s  = Slice(c, False, True)
        self.assertIs(type(s.start), int)
        self.assertIs(type(s.stop),  int)

    def test_start_end_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Slice start must be an integer, not 'x'$"):
            Slice(0, "x", 1)
        with self.assertRaisesRegex(TypeError,
                r"^Slice stop must be an integer, not 'x'$"):
            Slice(0, 1, "x")

    def test_start_end_out_of_range(self):
        c = Const(0, 8)
        with self.assertRaisesRegex(IndexError,
                r"^Cannot start slice 10 bits into 8-bit value$"):
            Slice(c, 10, 12)
        with self.assertRaisesRegex(IndexError,
                r"^Cannot stop slice 12 bits into 8-bit value$"):
            Slice(c, 0, 12)
        with self.assertRaisesRegex(IndexError,
                r"^Slice start 4 must be less than slice stop 2$"):
            Slice(c, 4, 2)
        with self.assertRaisesRegex(IndexError,
                r"^Cannot start slice -9 bits into 8-bit value$"):
            Slice(c, -9, -5)

    def test_repr(self):
        s1 = Const(10)[2]
        self.assertEqual(repr(s1), "(slice (const 4'd10) 2:3)")

    def test_const(self):
        a = Const.cast(Const(0x1234, 16)[4:12])
        self.assertEqual(a.value, 0x23)
        self.assertEqual(a.shape(), unsigned(8))
        a = Const.cast(Const(-4, signed(8))[1:6])
        self.assertEqual(a.value, 0x1e)
        self.assertEqual(a.shape(), unsigned(5))


class BitSelectTestCase(FHDLTestCase):
    def setUp(self):
        self.c = Const(0, 8)
        self.s = Signal(range(len(self.c)))

    def test_shape(self):
        s1 = self.c.bit_select(self.s, 2)
        self.assertIsInstance(s1, Part)
        self.assertEqual(s1.shape(), unsigned(2))
        self.assertIsInstance(s1.shape(), Shape)
        s2 = self.c.bit_select(self.s, 0)
        self.assertIsInstance(s2, Part)
        self.assertEqual(s2.shape(), unsigned(0))

    def test_stride(self):
        s1 = self.c.bit_select(self.s, 2)
        self.assertIsInstance(s1, Part)
        self.assertEqual(s1.stride, 1)

    def test_const(self):
        s1 = self.c.bit_select(1, 2)
        self.assertIsInstance(s1, Slice)
        self.assertRepr(s1, """(slice (const 8'd0) 1:3)""")

    def test_width_wrong(self):
        with self.assertRaises(TypeError):
            self.c.bit_select(self.s, -1)

    def test_repr(self):
        s = self.c.bit_select(self.s, 2)
        self.assertEqual(repr(s), "(part (const 8'd0) (sig s) 2 1)")

    def test_offset_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Part offset must be unsigned$"):
            self.c.bit_select(self.s.as_signed(), 1)


class WordSelectTestCase(FHDLTestCase):
    def setUp(self):
        self.c = Const(0, 8)
        self.s = Signal(range(len(self.c)))

    def test_shape(self):
        s1 = self.c.word_select(self.s, 2)
        self.assertIsInstance(s1, Part)
        self.assertEqual(s1.shape(), unsigned(2))
        self.assertIsInstance(s1.shape(), Shape)

    def test_stride(self):
        s1 = self.c.word_select(self.s, 2)
        self.assertIsInstance(s1, Part)
        self.assertEqual(s1.stride, 2)

    def test_const(self):
        s1 = self.c.word_select(1, 2)
        self.assertIsInstance(s1, Slice)
        self.assertRepr(s1, """(slice (const 8'd0) 2:4)""")

    def test_width_wrong(self):
        with self.assertRaises(TypeError):
            self.c.word_select(self.s, 0)
        with self.assertRaises(TypeError):
            self.c.word_select(self.s, -1)

    def test_repr(self):
        s = self.c.word_select(self.s, 2)
        self.assertEqual(repr(s), "(part (const 8'd0) (sig s) 2 2)")

    def test_offset_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Part offset must be unsigned$"):
            self.c.word_select(self.s.as_signed(), 1)


class CatTestCase(FHDLTestCase):
    def test_shape(self):
        c0 = Cat()
        self.assertEqual(c0.shape(), unsigned(0))
        self.assertIsInstance(c0.shape(), Shape)
        c1 = Cat(Const(10))
        self.assertEqual(c1.shape(), unsigned(4))
        c2 = Cat(Const(10), Const(1))
        self.assertEqual(c2.shape(), unsigned(5))
        c3 = Cat(Const(10), Const(1), Const(0))
        self.assertEqual(c3.shape(), unsigned(6))

    def test_repr(self):
        c1 = Cat(Const(10), Const(1))
        self.assertEqual(repr(c1), "(cat (const 4'd10) (const 1'd1))")

    def test_cast(self):
        c = Cat(1, 0)
        self.assertEqual(repr(c), "(cat (const 1'd1) (const 1'd0))")

    def test_str_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Object 'foo' cannot be converted to an Amaranth value$"):
            Cat("foo")

    def test_int_01(self):
        with warnings.catch_warnings():
            warnings.filterwarnings(action="error", category=SyntaxWarning)
            Cat(0, 1, 1, 0)

    def test_enum_wrong(self):
        class Color(Enum):
            RED  = 1
            BLUE = 2
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Argument #1 of Cat\(\) is an enumerated value <Color\.RED: 1> without "
                r"a defined shape used in bit vector context; define the enumeration by "
                r"inheriting from the class in amaranth\.lib\.enum and specifying "
                r"the 'shape=' keyword argument$"):
            c = Cat(Color.RED, Color.BLUE)
        self.assertEqual(repr(c), "(cat (const 2'd1) (const 2'd2))")

    def test_intenum_wrong(self):
        class Color(int, Enum):
            RED  = 1
            BLUE = 2
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Argument #1 of Cat\(\) is an enumerated value <Color\.RED: 1> without "
                r"a defined shape used in bit vector context; define the enumeration by "
                r"inheriting from the class in amaranth\.lib\.enum and specifying "
                r"the 'shape=' keyword argument$"):
            c = Cat(Color.RED, Color.BLUE)
        self.assertEqual(repr(c), "(cat (const 2'd1) (const 2'd2))")

    def test_int_wrong(self):
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Argument #1 of Cat\(\) is a bare integer 2 used in bit vector context; "
                r"specify the width explicitly using C\(2, 2\)$"):
            Cat(2)

    def test_const(self):
        a = Const.cast(Cat(Const(1, 1), Const(0, 1), Const(3, 2), Const(2, 2)))
        self.assertEqual(a.value, 0x2d)
        self.assertEqual(a.shape(), unsigned(6))
        a = Const.cast(Cat(Const(-4, 8), Const(-3, 8)))
        self.assertEqual(a.value, 0xfdfc)
        self.assertEqual(a.shape(), unsigned(16))


class ArrayTestCase(FHDLTestCase):
    def test_acts_like_array(self):
        a = Array([1,2,3])
        self.assertSequenceEqual(a, [1,2,3])
        self.assertEqual(a[1], 2)
        a[1] = 4
        self.assertSequenceEqual(a, [1,4,3])
        del a[1]
        self.assertSequenceEqual(a, [1,3])
        a.insert(1, 2)
        self.assertSequenceEqual(a, [1,2,3])

    def test_becomes_immutable(self):
        a = Array([1,2,3])
        s1 = Signal(range(len(a)))
        s2 = Signal(range(len(a)))
        v1 = a[s1]
        v2 = a[s2]
        with self.assertRaisesRegex(ValueError,
                r"^Array can no longer be mutated after it was indexed with a value at "):
            a[1] = 2
        with self.assertRaisesRegex(ValueError,
                r"^Array can no longer be mutated after it was indexed with a value at "):
            del a[1]
        with self.assertRaisesRegex(ValueError,
                r"^Array can no longer be mutated after it was indexed with a value at "):
            a.insert(1, 2)

    def test_index_value_castable(self):
        class MyValue(ValueCastable):
            def as_value(self):
                return Signal()

            def shape():
                return unsigned(1)

        a = Array([1,2,3])
        a[MyValue()]

    def test_repr(self):
        a = Array([1,2,3])
        self.assertEqual(repr(a), "(array mutable [1, 2, 3])")
        s = Signal(range(len(a)))
        v = a[s]
        self.assertEqual(repr(a), "(array [1, 2, 3])")


class ArrayProxyTestCase(FHDLTestCase):
    def test_index_shape(self):
        m = Array(Array(x * y for y in range(1, 4)) for x in range(1, 4))
        a = Signal(range(3))
        b = Signal(range(3))
        v = m[a][b]
        self.assertEqual(v.shape(), unsigned(4))

    def test_attr_shape(self):
        from collections import namedtuple
        pair = namedtuple("pair", ("p", "n"))
        a = Array(pair(i, -i) for i in range(10))
        s = Signal(range(len(a)))
        v = a[s]
        self.assertEqual(v.p.shape(), unsigned(4))
        self.assertEqual(v.n.shape(), signed(5))

    def test_attr_shape_signed(self):
        # [unsigned(1), unsigned(1)] → unsigned(1)
        a1 = Array([1, 1])
        v1 = a1[Const(0)]
        self.assertEqual(v1.shape(), unsigned(1))
        # [signed(1), signed(1)] → signed(1)
        a2 = Array([-1, -1])
        v2 = a2[Const(0)]
        self.assertEqual(v2.shape(), signed(1))
        # [unsigned(1), signed(2)] → signed(2)
        a3 = Array([1, -2])
        v3 = a3[Const(0)]
        self.assertEqual(v3.shape(), signed(2))
        # [unsigned(1), signed(1)] → signed(2); 1st operand padded with sign bit!
        a4 = Array([1, -1])
        v4 = a4[Const(0)]
        self.assertEqual(v4.shape(), signed(2))
        # [unsigned(2), signed(1)] → signed(3); 1st operand padded with sign bit!
        a5 = Array([1, -1])
        v5 = a5[Const(0)]
        self.assertEqual(v5.shape(), signed(2))

    def test_repr(self):
        a = Array([1, 2, 3])
        s = Signal(range(3))
        v = a[s]
        self.assertEqual(repr(v), "(proxy (array [1, 2, 3]) (sig s))")
        self.assertEqual(repr(v.as_value()), "(switch-value (sig s) (case 00 (const 1'd1)) (case 01 (const 2'd2)) (case 10 (const 2'd3)))")


class SignalTestCase(FHDLTestCase):
    def test_shape(self):
        s1 = Signal()
        self.assertEqual(s1.shape(), unsigned(1))
        self.assertIsInstance(s1.shape(), Shape)
        s2 = Signal(2)
        self.assertEqual(s2.shape(), unsigned(2))
        s3 = Signal(unsigned(2))
        self.assertEqual(s3.shape(), unsigned(2))
        s4 = Signal(signed(2))
        self.assertEqual(s4.shape(), signed(2))
        s5 = Signal(0)
        self.assertEqual(s5.shape(), unsigned(0))
        s6 = Signal(range(16))
        self.assertEqual(s6.shape(), unsigned(4))
        s7 = Signal(range(4, 16))
        self.assertEqual(s7.shape(), unsigned(4))
        s8 = Signal(range(-4, 16))
        self.assertEqual(s8.shape(), signed(5))
        s9 = Signal(range(-20, 16))
        self.assertEqual(s9.shape(), signed(6))
        s10 = Signal(range(0))
        self.assertEqual(s10.shape(), unsigned(0))
        s11 = Signal(range(1))
        self.assertEqual(s11.shape(), unsigned(0))

    def test_shape_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Width of an unsigned value must be zero or a positive integer, not -10$"):
            Signal(-10)

    def test_name(self):
        s1 = Signal()
        self.assertEqual(s1.name, "s1")
        s2 = Signal(name="sig")
        self.assertEqual(s2.name, "sig")
        s3 = Signal(name="")
        self.assertEqual(s3.name, "")

    def test_init(self):
        s1 = Signal(4, init=0b111, reset_less=True)
        self.assertEqual(s1.init, 0b111)
        self.assertEqual(s1.reset_less, True)
        s2 = Signal.like(s1, init=0b011)
        self.assertEqual(s2.init, 0b011)

    def test_init_enum(self):
        s1 = Signal(2, init=UnsignedEnum.BAR)
        self.assertEqual(s1.init, 2)
        with self.assertRaisesRegex(TypeError,
                r"^Initial value must be a constant-castable expression, "
                r"not <StringEnum\.FOO: 'a'>$"):
            Signal(1, init=StringEnum.FOO)

    def test_init_const_castable(self):
        s1 = Signal(4, init=Cat(Const(0, 1), Const(1, 1), Const(0, 2)))
        self.assertEqual(s1.init, 2)

    def test_init_shape_castable_const(self):
        class CastableFromHex(ShapeCastable):
            def as_shape(self):
                return unsigned(8)

            def __call__(self, value):
                return value

            def const(self, init):
                return int(init, 16)

            def from_bits(self, bits):
                return bits

        s1 = Signal(CastableFromHex(), init="aa")
        self.assertEqual(s1.init, 0xaa)

        with self.assertRaisesRegex(ValueError,
                r"^Constant returned by <.+?CastableFromHex.+?>\.const\(\) must have the shape "
                r"that it casts to, unsigned\(8\), and not unsigned\(1\)$"):
            Signal(CastableFromHex(), init="01")

    def test_init_shape_castable_enum_wrong(self):
        class EnumA(AmaranthEnum, shape=1):
            X = 1
        with self.assertRaisesRegex(TypeError,
                r"^Initial value must be a constant initializer of <enum 'EnumA'>$"):
            Signal(EnumA) # implied init=0

    def test_init_signed_mismatch(self):
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Initial value -2 is signed, but the signal shape is unsigned\(2\)$"):
            Signal(unsigned(2), init=-2)

    def test_init_wrong_too_wide(self):
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Initial value 2 will be truncated to the signal shape unsigned\(1\)$"):
            Signal(unsigned(1), init=2)
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Initial value 1 will be truncated to the signal shape signed\(1\)$"):
            Signal(signed(1), init=1)
        with self.assertWarnsRegex(SyntaxWarning,
                r"^Initial value -2 will be truncated to the signal shape signed\(1\)$"):
            Signal(signed(1), init=-2)

    def test_init_truncated(self):
        s1 = Signal(unsigned(2), init=-1)
        self.assertEqual(s1.init, 0b11)
        with warnings.catch_warnings():
            warnings.filterwarnings(action="ignore", category=SyntaxWarning)
            s2 = Signal(signed(2), init=-33)
            self.assertEqual(s2.init, -1)

    def test_init_wrong_fencepost(self):
        with self.assertRaisesRegex(SyntaxError,
                r"^Initial value 10 equals the non-inclusive end of the signal shape "
                r"range\(0, 10\); this is likely an off-by-one error$"):
            Signal(range(0, 10), init=10)
        with self.assertRaisesRegex(SyntaxError,
                r"^Initial value 0 equals the non-inclusive end of the signal shape "
                r"range\(0, 0\); this is likely an off-by-one error$"):
            Signal(range(0), init=0)

    def test_init_wrong_range(self):
        with self.assertRaisesRegex(SyntaxError,
                r"^Initial value 11 is not within the signal shape range\(0, 10\)$"):
            Signal(range(0, 10), init=11)
        with self.assertRaisesRegex(SyntaxError,
                r"^Initial value 0 is not within the signal shape range\(1, 10\)$"):
            Signal(range(1, 10), init=0)

    def test_reset(self):
        with self.assertWarnsRegex(DeprecationWarning,
                r"^`reset=` is deprecated, use `init=` instead$"):
            s1 = Signal(4, reset=0b111)
        self.assertEqual(s1.init, 0b111)
        with self.assertWarnsRegex(DeprecationWarning,
                r"^`Signal.reset` is deprecated, use `Signal.init` instead$"):
            self.assertEqual(s1.reset, 0b111)
        with self.assertWarnsRegex(DeprecationWarning,
                r"^`reset=` is deprecated, use `init=` instead$"):
            s2 = Signal.like(s1, reset=3)
        self.assertEqual(s2.init, 3)

    def test_reset_wrong(self):
        with self.assertRaisesRegex(ValueError,
                r"^Cannot specify both `reset` and `init`$"):
            Signal(4, reset=1, init=1)
        s1 = Signal(4)
        with self.assertRaisesRegex(ValueError,
                r"^Cannot specify both `reset` and `init`$"):
            Signal.like(s1, reset=1, init=1)

    def test_attrs(self):
        s1 = Signal()
        self.assertEqual(s1.attrs, {})
        s2 = Signal(attrs={"no_retiming": True})
        self.assertEqual(s2.attrs, {"no_retiming": True})

    def test_repr(self):
        s1 = Signal()
        self.assertEqual(repr(s1), "(sig s1)")
        s2 = Signal(name="")
        self.assertEqual(repr(s2), "(sig)")

    def test_like(self):
        s1 = Signal.like(Signal(4))
        self.assertEqual(s1.shape(), unsigned(4))
        s2 = Signal.like(Signal(range(-15, 1)))
        self.assertEqual(s2.shape(), signed(5))
        s3 = Signal.like(Signal(4, init=0b111, reset_less=True))
        self.assertEqual(s3.init, 0b111)
        self.assertEqual(s3.reset_less, True)
        s4 = Signal.like(Signal(attrs={"no_retiming": True}))
        self.assertEqual(s4.attrs, {"no_retiming": True})
        s5 = Signal.like(Signal(decoder=str))
        self.assertEqual(s5.decoder, str)
        s6 = Signal.like(10)
        self.assertEqual(s6.shape(), unsigned(4))
        s7 = [Signal.like(Signal(4))][0]
        self.assertEqual(s7.name, "$like")
        s8 = Signal.like(s1, name_suffix="_ff")
        self.assertEqual(s8.name, "s1_ff")

    def test_decoder(self):
        class Color(Enum):
            RED  = 1
            BLUE = 2
        s = Signal(decoder=Color)
        self.assertEqual(s.decoder, Color)
        self.assertRepr(s._format, f"(format-enum (sig s) '{Color.__qualname__}' (1 'RED') (2 'BLUE'))")

    def test_enum(self):
        s1 = Signal(UnsignedEnum)
        self.assertEqual(s1.shape(), unsigned(2))
        s2 = Signal(SignedEnum)
        self.assertEqual(s2.shape(), signed(2))
        self.assertRepr(s2._format, "(format-enum (sig s2) 'SignedEnum' (-1 'FOO') (0 'BAR') (1 'BAZ'))")

    def test_const_wrong(self):
        s1 = Signal()
        with self.assertRaisesRegex(TypeError,
                r"^Value \(sig s1\) cannot be converted to an Amaranth constant$"):
            Const.cast(s1)

    def test_format_simple(self):
        s = Signal()
        self.assertRepr(s._format, "(format '{}' (sig s))")


class ClockSignalTestCase(FHDLTestCase):
    def test_domain(self):
        s1 = ClockSignal()
        self.assertEqual(s1.domain, "sync")
        s2 = ClockSignal("pix")
        self.assertEqual(s2.domain, "pix")

        with self.assertRaisesRegex(TypeError,
                r"^Clock domain name must be a string, not 1$"):
            ClockSignal(1)

    def test_shape(self):
        s1 = ClockSignal()
        self.assertEqual(s1.shape(), unsigned(1))
        self.assertIsInstance(s1.shape(), Shape)

    def test_repr(self):
        s1 = ClockSignal()
        self.assertEqual(repr(s1), "(clk sync)")

    def test_wrong_name_comb(self):
        with self.assertRaisesRegex(ValueError,
                r"^Domain 'comb' does not have a clock$"):
            ClockSignal("comb")


class ResetSignalTestCase(FHDLTestCase):
    def test_domain(self):
        s1 = ResetSignal()
        self.assertEqual(s1.domain, "sync")
        s2 = ResetSignal("pix")
        self.assertEqual(s2.domain, "pix")

        with self.assertRaisesRegex(TypeError,
                r"^Clock domain name must be a string, not 1$"):
            ResetSignal(1)

    def test_shape(self):
        s1 = ResetSignal()
        self.assertEqual(s1.shape(), unsigned(1))
        self.assertIsInstance(s1.shape(), Shape)

    def test_repr(self):
        s1 = ResetSignal()
        self.assertEqual(repr(s1), "(rst sync)")

    def test_wrong_name_comb(self):
        with self.assertRaisesRegex(ValueError,
                r"^Domain 'comb' does not have a reset$"):
            ResetSignal("comb")


class MockValueCastable(ValueCastable):
    def __init__(self, dest):
        self.dest = dest

    def shape(self):
        return Value.cast(self.dest).shape()

    def as_value(self):
        return self.dest


class MockShapeCastableFormat(ShapeCastable):
    def __init__(self, dest):
        self.dest = dest

    def as_shape(self):
        return self.dest

    def __call__(self, value):
        return value

    def const(self, init):
        return Const(init, self.dest)

    def from_bits(self, bits):
        return bits

    def format(self, value, format_desc):
        return Format("_{}_{}_", Value.cast(value), format_desc)


class MockValueCastableFormat(ValueCastable):
    def __init__(self, dest):
        self.dest = dest

    def shape(self):
        return MockShapeCastableFormat(Value.cast(self.dest).shape())

    def as_value(self):
        return self.dest


class MockValueCastableNoFormat(ValueCastable):
    def __init__(self, dest):
        self.dest = dest

    def shape(self):
        return MockShapeCastable(Value.cast(self.dest).shape())

    def as_value(self):
        return self.dest


class MockShapeCastableFormatWrong(ShapeCastable):
    def __init__(self, dest):
        self.dest = dest

    def as_shape(self):
        return self.dest

    def __call__(self, value):
        return value

    def const(self, init):
        return Const(init, self.dest)

    def from_bits(self, bits):
        return bits

    def format(self, value, format_desc):
        return Value.cast(value)


class MockValueCastableFormatWrong(ValueCastable):
    def __init__(self, dest):
        self.dest = dest

    def shape(self):
        return MockShapeCastableFormatWrong(Value.cast(self.dest).shape())

    def as_value(self):
        return self.dest


class MockValueCastableCustomGetattr(ValueCastable):
    def __init__(self):
        pass

    def shape(self):
        assert False

    def as_value(self):
        return Const(0)

    def __getattr__(self, attr):
        assert False


class ValueCastableTestCase(FHDLTestCase):
    def test_no_override(self):
        with self.assertRaisesRegex(TypeError,
                r"^Class '.+\.MockValueCastableNoOverrideAsValue' deriving from 'ValueCastable' must "
                r"override the 'as_value' method$"):
            class MockValueCastableNoOverrideAsValue(ValueCastable):
                def __init__(self):
                    pass

        with self.assertRaisesRegex(TypeError,
                r"^Class '.+\.MockValueCastableNoOverrideShapec' deriving from 'ValueCastable' must "
                r"override the 'shape' method$"):
            class MockValueCastableNoOverrideShapec(ValueCastable):
                def __init__(self):
                    pass

                def as_value(self):
                    return Signal()

    def test_custom_getattr(self):
        vc = MockValueCastableCustomGetattr()
        vc.as_value() # shouldn't call __getattr__

    def test_recurse_bad(self):
        vc = MockValueCastable(None)
        vc.dest = vc
        with self.assertRaisesRegex(RecursionError,
                r"^Value-castable object <.+> casts to itself$"):
            Value.cast(vc)

    def test_recurse(self):
        vc = MockValueCastable(MockValueCastable(Signal()))
        self.assertIsInstance(Value.cast(vc), Signal)

    def test_abstract(self):
        with self.assertRaisesRegex(TypeError,
                r"^Can't instantiate abstract class ValueCastable$"):
            ValueCastable()


class ValueLikeTestCase(FHDLTestCase):
    def test_construct(self):
        with self.assertRaises(TypeError):
            ValueLike()

    def test_subclass(self):
        self.assertTrue(issubclass(Value, ValueLike))
        self.assertTrue(issubclass(MockValueCastable, ValueLike))
        self.assertTrue(issubclass(int, ValueLike))
        self.assertFalse(issubclass(range, ValueLike))
        self.assertFalse(issubclass(EnumMeta, ValueLike))
        self.assertTrue(issubclass(Enum, ValueLike))
        self.assertFalse(issubclass(str, ValueLike))
        self.assertTrue(issubclass(ValueLike, ValueLike))

    def test_isinstance(self):
        self.assertTrue(isinstance(Const(0, 2), ValueLike))
        self.assertTrue(isinstance(MockValueCastable(Const(0, 2)), ValueLike))
        self.assertTrue(isinstance(2, ValueLike))
        self.assertTrue(isinstance(-2, ValueLike))
        self.assertFalse(isinstance(range(10), ValueLike))

    def test_enum(self):
        class EnumA(Enum):
            A = 1
            B = 2
        class EnumB(Enum):
            A = "a"
            B = "b"
        class EnumC(Enum):
            A = Cat(Const(1, 2), Const(0, 2))
        class EnumD(Enum):
            A = 1
            B = "a"
        self.assertTrue(issubclass(EnumA, ValueLike))
        self.assertFalse(issubclass(EnumB, ValueLike))
        self.assertTrue(issubclass(EnumC, ValueLike))
        self.assertFalse(issubclass(EnumD, ValueLike))
        self.assertTrue(isinstance(EnumA.A, ValueLike))
        self.assertFalse(isinstance(EnumB.A, ValueLike))
        self.assertTrue(isinstance(EnumC.A, ValueLike))
        self.assertFalse(isinstance(EnumD.A, ValueLike))


class InitialTestCase(FHDLTestCase):
    def test_initial(self):
        i = Initial()
        self.assertEqual(i.shape(), unsigned(1))


class FormatTestCase(FHDLTestCase):
    def test_construct(self):
        a = Signal()
        b = Signal()
        c = Signal()
        self.assertRepr(Format("abc"), "(format 'abc')")
        fmt = Format("{{abc}}")
        self.assertRepr(fmt, "(format '{{abc}}')")
        self.assertEqual(fmt._chunks, ("{abc}",))
        fmt = Format("{abc}", abc="{def}")
        self.assertRepr(fmt, "(format '{{def}}')")
        self.assertEqual(fmt._chunks, ("{def}",))
        fmt = Format("a: {a:0{b}}, b: {b}", a=13, b=4)
        self.assertRepr(fmt, "(format 'a: 0013, b: 4')")
        fmt = Format("a: {a:0{b}x}, b: {b}", a=a, b=4)
        self.assertRepr(fmt, "(format 'a: {:04x}, b: 4' (sig a))")
        fmt = Format("a: {a}, b: {b}, a: {a}", a=a, b=b)
        self.assertRepr(fmt, "(format 'a: {}, b: {}, a: {}' (sig a) (sig b) (sig a))")
        fmt = Format("a: {0}, b: {1}, a: {0}", a, b)
        self.assertRepr(fmt, "(format 'a: {}, b: {}, a: {}' (sig a) (sig b) (sig a))")
        fmt = Format("a: {}, b: {}", a, b)
        self.assertRepr(fmt, "(format 'a: {}, b: {}' (sig a) (sig b))")
        subfmt = Format("a: {:2x}, b: {:3x}", a, b)
        fmt = Format("sub: {}, c: {:4x}", subfmt, c)
        self.assertRepr(fmt, "(format 'sub: a: {:2x}, b: {:3x}, c: {:4x}' (sig a) (sig b) (sig c))")

    def test_construct_valuecastable(self):
        a = Signal()
        b = MockValueCastable(a)
        fmt = Format("{:x}", b)
        self.assertRepr(fmt, "(format '{:x}' (sig a))")
        c = MockValueCastableFormat(a)
        fmt = Format("{:meow}", c)
        self.assertRepr(fmt, "(format '_{}_meow_' (sig a))")
        d = MockValueCastableNoFormat(a)
        fmt = Format("{:x}", d)
        self.assertRepr(fmt, "(format '{:x}' (sig a))")
        e = MockValueCastableFormat(a)
        fmt = Format("{!v:x}", e)
        self.assertRepr(fmt, "(format '{:x}' (sig a))")

    def test_construct_wrong(self):
        a = Signal()
        b = Signal(signed(16))
        with self.assertRaisesRegex(ValueError,
                r"^cannot switch from manual field specification to automatic field numbering$"):
            Format("{0}, {}", a, b)
        with self.assertRaisesRegex(ValueError,
                r"^cannot switch from automatic field numbering to manual field specification$"):
            Format("{}, {1}", a, b)
        with self.assertRaisesRegex(ValueError,
                r"^Format specifiers \('s'\) cannot be used for 'Format' objects$"):
            Format("{:s}", Format(""))
        with self.assertRaisesRegex(ValueError,
                r"^format positional argument 1 was not used$"):
            Format("{}", a, b)
        with self.assertRaisesRegex(ValueError,
                r"^format keyword argument 'b' was not used$"):
            Format("{a}", a=a, b=b)
        with self.assertRaisesRegex(ValueError,
                r"^Invalid format specifier 'meow'$"):
            Format("{a:meow}", a=a)
        with self.assertRaisesRegex(ValueError,
                r"^Alignment '\^' is not supported$"):
            Format("{a:^13}", a=a)
        with self.assertRaisesRegex(ValueError,
                r"^Grouping option ',' is not supported$"):
            Format("{a:,}", a=a)
        with self.assertRaisesRegex(ValueError,
                r"^Presentation type 'n' is not supported$"):
            Format("{a:n}", a=a)
        with self.assertRaisesRegex(ValueError,
                r"^Cannot print signed value with format specifier 'c'$"):
            Format("{b:c}", b=b)
        with self.assertRaisesRegex(ValueError,
                r"^Value width must be divisible by 8 with format specifier 's'$"):
            Format("{a:s}", a=a)
        with self.assertRaisesRegex(ValueError,
                r"^Alignment '=' is not allowed with format specifier 'c'$"):
            Format("{a:=13c}", a=a)
        with self.assertRaisesRegex(ValueError,
                r"^Sign is not allowed with format specifier 'c'$"):
            Format("{a:+13c}", a=a)
        with self.assertRaisesRegex(ValueError,
                r"^Zero fill is not allowed with format specifier 'c'$"):
            Format("{a:013c}", a=a)
        with self.assertRaisesRegex(ValueError,
                r"^Alternate form is not allowed with format specifier 'c'$"):
            Format("{a:#13c}", a=a)
        with self.assertRaisesRegex(ValueError,
                r"^Cannot specify '_' with format specifier 'c'$"):
            Format("{a:_c}", a=a)

    def test_construct_valuecastable_wrong(self):
        a = Signal()
        b = MockValueCastableFormatWrong(a)
        with self.assertRaisesRegex(TypeError,
                r"^`ShapeCastable.format` must return a 'Format' instance, "
                r"not \(sig a\)$"):
            fmt = Format("{:x}", b)

    def test_plus(self):
        a = Signal()
        b = Signal()
        fmt_a = Format("a = {};", a)
        fmt_b = Format("b = {};", b)
        fmt = fmt_a + fmt_b
        self.assertRepr(fmt, "(format 'a = {};b = {};' (sig a) (sig b))")
        self.assertEqual(fmt._chunks[2], ";b = ")

    def test_plus_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^unsupported operand type\(s\) for \+: 'Format' and 'str'$"):
            Format("") + ""

    def test_format_wrong(self):
        fmt = Format("")
        with self.assertRaisesRegex(TypeError,
                r"^Format object .* cannot be converted to string."):
            f"{fmt}"


class FormatEnumTestCase(FHDLTestCase):
    def test_construct(self):
        a = Signal(3)
        fmt = Format.Enum(a, {1: "A", 2: "B", 3: "C"})
        self.assertRepr(fmt, "(format-enum (sig a) - (1 'A') (2 'B') (3 'C'))")
        self.assertRepr(Format("{}", fmt), """
            (format '{:s}' (switch-value (sig a)
                (case 001 (const 8'd65))
                (case 010 (const 8'd66))
                (case 011 (const 8'd67))
                (default (const 72'd1723507152241428428123))
            ))
        """)

        class MyEnum(Enum):
            A = 0
            B = 3
            C = 4

        fmt = Format.Enum(a, MyEnum, name="MyEnum")
        self.assertRepr(fmt, "(format-enum (sig a) 'MyEnum' (0 'A') (3 'B') (4 'C'))")
        self.assertRepr(Format("{}", fmt), """
            (format '{:s}' (switch-value (sig a)
                (case 000 (const 8'd65))
                (case 011 (const 8'd66))
                (case 100 (const 8'd67))
                (default (const 72'd1723507152241428428123))
            ))
        """)

    def test_construct_wrong(self):
        a = Signal(3)
        with self.assertRaisesRegex(TypeError,
                r"^Variant values must be integers, not 'a'$"):
            Format.Enum(a, {"a": "B"})
        with self.assertRaisesRegex(TypeError,
                r"^Variant names must be strings, not 123$"):
            Format.Enum(a, {1: 123})
        with self.assertRaisesRegex(TypeError,
                r"^Enum name must be a string or None, not 123$"):
            Format.Enum(a, {}, name=123)


class FormatStructTestCase(FHDLTestCase):
    def test_construct(self):
        sig = Signal(3)
        fmt = Format.Struct(sig, {"a": Format("{}", sig[0]), "b": Format("{}", sig[1:3])})
        self.assertRepr(fmt, """
        (format-struct (sig sig)
            ('a' (format '{}' (slice (sig sig) 0:1)))
            ('b' (format '{}' (slice (sig sig) 1:3)))
        )
        """)
        self.assertRepr(Format("{}", fmt), """
            (format '{{a={}, b={}}}'
                (slice (sig sig) 0:1)
                (slice (sig sig) 1:3)
            )
        """)

    def test_construct_wrong(self):
        sig = Signal(3)
        with self.assertRaisesRegex(TypeError,
                r"^Field names must be strings, not 1$"):
            Format.Struct(sig, {1: Format("{}", sig[1:3])})
        with self.assertRaisesRegex(TypeError,
                r"^Field format must be a 'Format', not \(slice \(sig sig\) 1:3\)$"):
            Format.Struct(sig, {"a": sig[1:3]})


class FormatArrayTestCase(FHDLTestCase):
    def test_construct(self):
        sig = Signal(4)
        fmt = Format.Array(sig, [Format("{}", sig[0:2]), Format("{}", sig[2:4])])
        self.assertRepr(fmt, """
        (format-array (sig sig)
            (format '{}' (slice (sig sig) 0:2))
            (format '{}' (slice (sig sig) 2:4))
        )
        """)
        self.assertRepr(Format("{}", fmt), """
            (format '[{}, {}]'
                (slice (sig sig) 0:2)
                (slice (sig sig) 2:4)
            )
        """)

    def test_construct_wrong(self):
        sig = Signal(3)
        with self.assertRaisesRegex(TypeError,
                r"^Field format must be a 'Format', not \(slice \(sig sig\) 1:3\)$"):
            Format.Array(sig, [sig[1:3]])


class PrintTestCase(FHDLTestCase):
    def test_construct(self):
        a = Signal()
        b = Signal()
        p = Print("abc")
        self.assertRepr(p, "(print (format 'abc\\n'))")
        p = Print("abc", "def")
        self.assertRepr(p, "(print (format 'abc def\\n'))")
        p = Print("abc", b)
        self.assertRepr(p, "(print (format 'abc {}\\n' (sig b)))")
        p = Print(a, b, end="", sep=", ")
        self.assertRepr(p, "(print (format '{}, {}' (sig a) (sig b)))")
        p = Print(Format("a: {a:04x}", a=a))
        self.assertRepr(p, "(print (format 'a: {:04x}\\n' (sig a)))")

    def test_construct_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^'sep' must be a string, not 13$"):
            Print("", sep=13)
        with self.assertRaisesRegex(TypeError,
                r"^'end' must be a string, not 13$"):
            Print("", end=13)


class AssertTestCase(FHDLTestCase):
    def test_construct(self):
        a = Signal()
        b = Signal()
        p = Assert(a)
        self.assertRepr(p, "(assert (sig a))")
        p = Assert(a, "abc")
        self.assertRepr(p, "(assert (sig a) (format 'abc'))")
        p = Assert(a, Format("a = {}, b = {}", a, b))
        self.assertRepr(p, "(assert (sig a) (format 'a = {}, b = {}' (sig a) (sig b)))")

    def test_construct_wrong(self):
        a = Signal()
        b = Signal()
        with self.assertRaisesRegex(TypeError,
                r"^Property message must be None, str, or Format, not \(sig b\)$"):
            Assert(a, b)


class SwitchTestCase(FHDLTestCase):
    def test_default_case(self):
        s = Switch(Const(0), [(None, [], None)])
        self.assertEqual(s.cases, ((None, [], None),))

    def test_int_case(self):
        s = Switch(Const(0, 8), [(10, [], None)])
        self.assertEqual(s.cases, ((("00001010",), [], None),))

    def test_int_neg_case(self):
        s = Switch(Const(0, signed(8)), [(-10, [], None)])
        self.assertEqual(s.cases, ((("11110110",), [], None),))

    def test_int_zero_width(self):
        s = Switch(Const(0, 0), [(0, [], None)])
        self.assertEqual(s.cases, ((("",), [], None),))

    def test_int_zero_width_enum(self):
        class ZeroEnum(Enum):
            A = 0
        s = Switch(Const(0, 0), [(ZeroEnum.A, [], None)])
        self.assertEqual(s.cases, ((("",), [], None),))

    def test_enum_case(self):
        s = Switch(Const(0, UnsignedEnum), [(UnsignedEnum.FOO, [], None)])
        self.assertEqual(s.cases, ((("01",), [], None),))

    def test_str_case(self):
        s = Switch(Const(0, 8), [("0000 11\t01", [], None)])
        self.assertEqual(s.cases, ((("00001101",), [], None),))

    def test_two_cases(self):
        s = Switch(Const(0, 8), [(("00001111", 123), [], None)])
        self.assertEqual(s.cases, ((("00001111", "01111011"), [], None),))


class IOValueTestCase(FHDLTestCase):
    def test_ioport(self):
        a = IOPort(4)
        self.assertEqual(len(a), 4)
        self.assertEqual(a.attrs, {})
        self.assertEqual(a.metadata, (None, None, None, None))
        self.assertRepr(a, "(io-port a)")
        b = IOPort(3, name="b", attrs={"a": "b"}, metadata=["x", "y", "z"])
        self.assertEqual(len(b), 3)
        self.assertEqual(b.attrs, {"a": "b"})
        self.assertEqual(b.metadata, ("x", "y", "z"))
        self.assertRepr(b, "(io-port b)")

    def test_ioport_wrong(self):
        with self.assertRaisesRegex(TypeError,
                r"^Name must be a string, not 3$"):
            a = IOPort(2, name=3)
        with self.assertRaises(TypeError):
            a = IOPort("a")
        with self.assertRaises(TypeError):
            a = IOPort(8, attrs=3)
        with self.assertRaises(TypeError):
            a = IOPort(8, metadata=3)
        with self.assertRaisesRegex(ValueError,
                r"^Metadata length \(3\) doesn't match port width \(2\)$"):
            a = IOPort(2, metadata=["a", "b", "c"])

    def test_ioslice(self):
        a = IOPort(8, metadata=["a", "b", "c", "d", "e", "f", "g", "h"])
        s = a[2:5]
        self.assertEqual(len(s), 3)
        self.assertEqual(s.metadata, ("c", "d", "e"))
        self.assertRepr(s, "(io-slice (io-port a) 2:5)")
        s = a[-5:-2]
        self.assertEqual(len(s), 3)
        self.assertEqual(s.metadata, ("d", "e", "f"))
        self.assertRepr(s, "(io-slice (io-port a) 3:6)")
        s = IOSlice(a, -5, -2)
        self.assertEqual(len(s), 3)
        self.assertEqual(s.metadata, ("d", "e", "f"))
        self.assertRepr(s, "(io-slice (io-port a) 3:6)")
        s = a[5]
        self.assertEqual(len(s), 1)
        self.assertEqual(s.metadata, ("f",))
        self.assertRepr(s, "(io-slice (io-port a) 5:6)")
        s = a[-1]
        self.assertEqual(len(s), 1)
        self.assertEqual(s.metadata, ("h",))
        self.assertRepr(s, "(io-slice (io-port a) 7:8)")
        s = a[::2]
        self.assertEqual(len(s), 4)
        self.assertEqual(s.metadata, ("a", "c", "e", "g"))
        self.assertRepr(s, "(io-cat (io-slice (io-port a) 0:1) (io-slice (io-port a) 2:3) (io-slice (io-port a) 4:5) (io-slice (io-port a) 6:7))")

    def test_ioslice_wrong(self):
        a = IOPort(8)
        with self.assertRaises(IndexError):
            a[8]
        with self.assertRaises(IndexError):
            a[-9]
        with self.assertRaises(TypeError):
            a["a"]
        with self.assertRaises(IndexError):
            IOSlice(a, 0, 9)
        with self.assertRaises(IndexError):
            IOSlice(a, -10, 8)
        with self.assertRaises(TypeError):
            IOSlice(a, 0, "a")
        with self.assertRaises(TypeError):
            IOSlice(a, "a", 8)
        with self.assertRaises(IndexError):
            a[5:3]

    def test_iocat(self):
        a = IOPort(3, name="a", metadata=["a", "b", "c"])
        b = IOPort(2, name="b", metadata=["x", "y"])
        c = Cat(a, b)
        self.assertEqual(len(c), 5)
        self.assertEqual(c.metadata, ("a", "b", "c", "x", "y"))
        self.assertRepr(c, "(io-cat (io-port a) (io-port b))")
        c = Cat(a, Cat())
        self.assertEqual(len(c), 3)
        self.assertEqual(c.metadata, ("a", "b", "c"))
        self.assertRepr(c, "(io-cat (io-port a) (io-cat ))")
        c = Cat(a, Cat()[:])
        self.assertEqual(len(c), 3)
        self.assertRepr(c, "(io-cat (io-port a) (io-cat ))")

    def test_iocat_wrong(self):
        a = IOPort(3, name="a")
        b = Signal()
        with self.assertRaisesRegex(TypeError,
                r"^Object \(sig b\) cannot be converted to an IO value$"):
            Cat(a, b)

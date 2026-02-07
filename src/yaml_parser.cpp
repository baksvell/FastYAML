#include "fastyaml/yaml_parser.hpp"
#include <algorithm>
#include <cctype>
#include <cmath>
#include <limits>
#include <sstream>

#ifdef __AVX2__
#include <immintrin.h>
#endif

// Cross-platform count trailing zeros
#ifdef _MSC_VER
#include <intrin.h>
inline int ctz(unsigned int x) {
    unsigned long index;
    _BitScanForward(&index, x);
    return (int)index;
}
inline int ctz(unsigned long long x) {
    unsigned long index;
    _BitScanForward64(&index, x);
    return (int)index;
}
#else
inline int ctz(unsigned int x) {
    return __builtin_ctz(x);
}
inline int ctz(unsigned long long x) {
    return __builtin_ctzll(x);
}
#endif

namespace fastyaml {

namespace simd_utils {

inline bool is_whitespace(char c) {
    return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

inline bool is_whitespace_no_nl(char c) {
    return c == ' ' || c == '\t' || c == '\r';
}

#if defined(__AVX2__)
const char* skip_whitespace(const char* ptr, const char* end) {
    if (end - ptr < 32) {
        while (ptr < end && is_whitespace(*ptr)) ++ptr;
        return ptr;
    }
    const __m256i space = _mm256_set1_epi8(' ');
    const __m256i tab = _mm256_set1_epi8('\t');
    const __m256i cr = _mm256_set1_epi8('\r');
    const __m256i nl = _mm256_set1_epi8('\n');
    while (end - ptr >= 32) {
        __m256i chunk = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(ptr));
        __m256i combined = _mm256_or_si256(
            _mm256_or_si256(_mm256_cmpeq_epi8(chunk, space), _mm256_cmpeq_epi8(chunk, tab)),
            _mm256_or_si256(_mm256_cmpeq_epi8(chunk, cr), _mm256_cmpeq_epi8(chunk, nl)));
        unsigned int mask = static_cast<unsigned int>(_mm256_movemask_epi8(combined));
        if (mask != 0xFFFFFFFFU) {
            return ptr + ctz(~mask);
        }
        ptr += 32;
    }
    while (ptr < end && is_whitespace(*ptr)) ++ptr;
    return ptr;
}

const char* skip_whitespace_no_nl(const char* ptr, const char* end) {
    if (end - ptr < 32) {
        while (ptr < end && is_whitespace_no_nl(*ptr)) ++ptr;
        return ptr;
    }
    const __m256i space = _mm256_set1_epi8(' ');
    const __m256i tab = _mm256_set1_epi8('\t');
    const __m256i cr = _mm256_set1_epi8('\r');
    while (end - ptr >= 32) {
        __m256i chunk = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(ptr));
        __m256i combined = _mm256_or_si256(
            _mm256_or_si256(_mm256_cmpeq_epi8(chunk, space), _mm256_cmpeq_epi8(chunk, tab)),
            _mm256_cmpeq_epi8(chunk, cr));
        unsigned int mask = static_cast<unsigned int>(_mm256_movemask_epi8(combined));
        if (mask != 0xFFFFFFFFU) {
            return ptr + ctz(~mask);
        }
        ptr += 32;
    }
    while (ptr < end && is_whitespace_no_nl(*ptr)) ++ptr;
    return ptr;
}

const char* find_char_simd(const char* ptr, const char* end, char c) {
    if (end - ptr < 32) {
        while (ptr < end && *ptr != c) ++ptr;
        return ptr;
    }
    const __m256i target = _mm256_set1_epi8(c);
    while (end - ptr >= 32) {
        __m256i chunk = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(ptr));
        unsigned int mask = static_cast<unsigned int>(_mm256_movemask_epi8(_mm256_cmpeq_epi8(chunk, target)));
        if (mask != 0) return ptr + ctz(mask);
        ptr += 32;
    }
    while (ptr < end && *ptr != c) ++ptr;
    return ptr;
}
#else
const char* skip_whitespace(const char* ptr, const char* end) {
    while (ptr < end && is_whitespace(*ptr)) ++ptr;
    return ptr;
}
const char* skip_whitespace_no_nl(const char* ptr, const char* end) {
    while (ptr < end && is_whitespace_no_nl(*ptr)) ++ptr;
    return ptr;
}
const char* find_char_simd(const char* ptr, const char* end, char c) {
    while (ptr < end && *ptr != c) ++ptr;
    return ptr;
}
#endif

const char* find_char_in_line(const char* ptr, const char* end, char c) {
    const char* line_end = find_char_simd(ptr, end, '\n');
    return find_char_simd(ptr, line_end, c);
}

}  // namespace simd_utils

// YamlParser implementation
YamlParser::YamlParser() : current_(nullptr), end_(nullptr) {}

YamlParser::~YamlParser() = default;

void YamlParser::set_error(const std::string& message) {
    if (error_message_.empty()) {
        error_message_ = message;
    }
}

void YamlParser::skip_whitespace() {
    current_ = simd_utils::skip_whitespace(current_, end_);
}

void YamlParser::skip_whitespace_no_nl() {
    current_ = simd_utils::skip_whitespace_no_nl(current_, end_);
}

void YamlParser::skip_comment() {
    if (!eof() && *current_ == '#') {
        while (!eof() && *current_ != '\n') {
            advance();
        }
    }
}

void YamlParser::expect_char(char c) {
    if (eof() || *current_ != c) {
        set_error(std::string("Expected '") + c + "'");
        return;
    }
    advance();
}

bool YamlParser::peek_char(char c) {
    return !eof() && *current_ == c;
}

char YamlParser::peek() {
    return eof() ? '\0' : *current_;
}

char YamlParser::advance() {
    if (eof()) return '\0';
    return *current_++;
}

bool YamlParser::eof() {
    return current_ >= end_;
}

int YamlParser::get_current_indent() {
    const char* p = current_;
    int indent = 0;
    while (p < end_ && (*p == ' ' || *p == '\t')) {
        indent += (*p == '\t') ? 2 : 1;  // treat tab as 2 spaces for simplicity
        ++p;
    }
    return indent;
}

void YamlParser::skip_to_next_line() {
    while (!eof() && *current_ != '\n') advance();
    if (!eof()) advance();  // skip newline
}

void YamlParser::skip_blank_lines() {
    while (!eof()) {
        skip_whitespace_no_nl();
        if (eof()) break;
        if (*current_ == '\n') {
            advance();
        } else if (*current_ == '#') {
            skip_comment();
        } else {
            break;
        }
    }
}

void YamlParser::skip_blank_lines_only() {
    while (!eof()) {
        const char* p = current_;
        while (p < end_ && *p != '\n' && (*p == ' ' || *p == '\t')) ++p;
        if (p >= end_) break;
        if (*p == '\n') {
            skip_to_next_line();
            continue;
        }
        if (*p == '#') {
            skip_to_next_line();
            continue;
        }
        break;
    }
}

void YamlParser::skip_to_next_content_line() {
    while (!eof()) {
        if (*current_ == '\n') {
            advance();
            continue;
        }
        // At start of a line — check if blank or comment
        const char* p = current_;
        while (p < end_ && *p != '\n' && (*p == ' ' || *p == '\t')) ++p;
        if (p >= end_) break;
        if (*p == '\n') {
            skip_to_next_line();
            continue;
        }
        if (*p == '#') {
            skip_to_next_line();
            continue;
        }
        break;  // Content line — leave current_ at line start (with indent)
    }
}

bool YamlParser::at_line_start() {
    const char* p = current_;
    while (p > end_ - (end_ - current_)) {
        --p;
        if (p < end_) break;
    }
    if (current_ == end_) return true;
    const char* line_start = current_;
    while (line_start > end_ - 1000 && line_start[-1] != '\n') --line_start;
    return current_ == line_start || simd_utils::is_whitespace(*(current_ - 1));
}

std::string YamlParser::parse_escape_sequence() {
    if (eof()) return "";
    char c = advance();
    switch (c) {
        case 'n': return "\n";
        case 'r': return "\r";
        case 't': return "\t";
        case '\\': return "\\";
        case '"': return "\"";
        case '\'': return "'";
        default: return std::string(1, c);
    }
}

String YamlParser::parse_quoted_string(char quote) {
    expect_char(quote);
    std::string result;
    while (!eof() && *current_ != quote) {
        if (*current_ == '\\') {
            advance();
            result += parse_escape_sequence();
        } else {
            result += advance();
        }
    }
    if (!eof()) advance();  // closing quote
    return result;
}

void YamlParser::merge_into(Mapping& target, const YamlValue& val) {
    if (auto* mp = std::get_if<MappingPtr>(&val)) {
        for (const auto& [k, v] : (*mp)->values) {
            target.set(k, v);
        }
    } else if (auto* sp = std::get_if<SequencePtr>(&val)) {
        for (const auto& elem : (*sp)->elements) {
            if (auto* m = std::get_if<MappingPtr>(&elem)) {
                for (const auto& [k, v] : (*m)->values) {
                    target.set(k, v);
                }
            }
        }
    }
}

std::optional<std::string> YamlParser::try_parse_anchor() {
    if (eof() || *current_ != '&') return std::nullopt;
    const char* p = current_ + 1;
    while (p < end_ && (std::isalnum(static_cast<unsigned char>(*p)) || *p == '_' || *p == '-')) ++p;
    if (p == current_ + 1) return std::nullopt;
    std::string name(current_ + 1, p);
    current_ = p;
    return name;
}

std::optional<YamlValue> YamlParser::try_parse_alias() {
    if (eof() || *current_ != '*') return std::nullopt;
    const char* p = current_ + 1;
    while (p < end_ && (std::isalnum(static_cast<unsigned char>(*p)) || *p == '_' || *p == '-')) ++p;
    if (p == current_ + 1) return std::nullopt;
    std::string name(current_ + 1, p);
    current_ = p;
    auto it = anchors_.find(name);
    if (it == anchors_.end()) {
        set_error("Unknown alias: *" + name);
        return YamlValue(Null{});
    }
    return it->second;
}

std::optional<YamlValue> YamlParser::try_parse_bool() {
    const char* p = current_;
    if (end_ - p >= 4 && (p[0] == 't' || p[0] == 'T') && (p[1] == 'r' || p[1] == 'R') &&
        (p[2] == 'u' || p[2] == 'U') && (p[3] == 'e' || p[3] == 'E')) {
        if (end_ - p == 4 || !std::isalnum(static_cast<unsigned char>(p[4])) && p[4] != '_') {
            current_ = p + 4;
            return YamlValue(true);
        }
    }
    if (end_ - p >= 5 && (p[0] == 'f' || p[0] == 'F') && (p[1] == 'a' || p[1] == 'A') &&
        (p[2] == 'l' || p[2] == 'L') && (p[3] == 's' || p[3] == 'S') && (p[4] == 'e' || p[4] == 'E')) {
        if (end_ - p == 5 || !std::isalnum(static_cast<unsigned char>(p[5])) && p[5] != '_') {
            current_ = p + 5;
            return YamlValue(false);
        }
    }
    return std::nullopt;
}

std::optional<YamlValue> YamlParser::try_parse_null() {
    const char* p = current_;
    if (end_ - p >= 4 && (p[0] == 'n' || p[0] == 'N') && (p[1] == 'u' || p[1] == 'U') &&
        (p[2] == 'l' || p[2] == 'L') && (p[3] == 'l' || p[3] == 'L')) {
        if (end_ - p == 4 || !std::isalnum(static_cast<unsigned char>(p[4])) && p[4] != '_') {
            current_ = p + 4;
            return YamlValue(Null{});
        }
    }
    if (end_ - p >= 1 && *p == '~') {
        if (end_ - p == 1 || !std::isalnum(static_cast<unsigned char>(p[1])) && p[1] != '_') {
            current_ = p + 1;
            return YamlValue(Null{});
        }
    }
    return std::nullopt;
}

std::optional<YamlValue> YamlParser::try_parse_number() {
    const char* start = current_;
    if (eof()) return std::nullopt;
    bool negative = false;
    if (*current_ == '-') {
        negative = true;
        advance();
    } else if (*current_ == '+') {
        advance();
    }
    if (eof() || !std::isdigit(static_cast<unsigned char>(*current_))) {
        current_ = start;
        return std::nullopt;
    }
    const char* p = current_;
    bool has_dot = false;
    bool has_exp = false;
    int dot_count = 0;
    while (p < end_) {
        char c = *p;
        if (std::isdigit(static_cast<unsigned char>(c))) {
            ++p;
        } else if (c == '.' && !has_exp) {
            has_dot = true;
            ++dot_count;
            ++p;
        } else if ((c == 'e' || c == 'E') && !has_exp) {
            has_exp = true;
            ++p;
            if (p < end_ && (*p == '+' || *p == '-')) ++p;
        } else {
            break;
        }
    }
    std::string num_str(start, p);
    current_ = p;
    if (has_dot && !has_exp && dot_count > 1) {
        current_ = start;
        return std::nullopt;  // IP-like (192.168.1.1), keep as string
    }
    if (has_dot || has_exp) {
        try {
            double val = std::stod(num_str);
            return YamlValue(val);
        } catch (...) {
            current_ = start;
            return std::nullopt;
        }
    } else {
        try {
            int64_t val = std::stoll(num_str);
            return YamlValue(val);
        } catch (...) {
            current_ = start;
            return std::nullopt;
        }
    }
}

String YamlParser::parse_unquoted_scalar() {
    std::string result;
    while (!eof()) {
        char c = *current_;
        if (c == '#' || c == '\n' || c == '|' || c == '>' || c == '&' || c == '*') {
            break;
        }
        if (c == ':') {
            // Break only if colon could be key-value separator (followed by space/tab/newline)
            const char* next = current_ + 1;
            if (next >= end_ || *next == ' ' || *next == '\t' || *next == '\n') break;
            // Colon is part of value (nginx:1.14, localhost:8080, https://...)
        }
        if (c == ' ' || c == '\t') {
            const char* next = current_;
            while (next < end_ && (*next == ' ' || *next == '\t')) ++next;
            if (next < end_ && *next == '\n') break;
            if (next < end_ && *next == '#') break;
        }
        result += advance();
    }
    // Trim trailing whitespace
    while (!result.empty() && (result.back() == ' ' || result.back() == '\t')) {
        result.pop_back();
    }
    return result;
}

String YamlParser::parse_scalar() {
    skip_whitespace_no_nl();
    if (eof()) return "";
    if (*current_ == '"') return parse_quoted_string('"');
    if (*current_ == '\'') return parse_quoted_string('\'');
    return parse_unquoted_scalar();
}

String YamlParser::parse_scalar_flow() {
    skip_whitespace_no_nl();
    if (eof()) return "";
    if (*current_ == '"') return parse_quoted_string('"');
    if (*current_ == '\'') return parse_quoted_string('\'');
    std::string result;
    while (!eof()) {
        char c = *current_;
        if (c == ',' || c == ']' || c == '}' || c == '[' || c == '#' || c == '\n') break;
        if (c == ' ' || c == '\t') {
            const char* next = current_;
            while (next < end_ && (*next == ' ' || *next == '\t')) ++next;
            if (next < end_ && (*next == '\n' || *next == '#' || *next == ',' || *next == ']' || *next == '}')) break;
        }
        if (c == ':') {
            const char* n = current_ + 1;
            if (n >= end_ || *n == ' ' || *n == '\t' || *n == '\n' || *n == ',' || *n == '}') break;
        }
        result += advance();
    }
    while (!result.empty() && (result.back() == ' ' || result.back() == '\t')) result.pop_back();
    return result;
}

String YamlParser::parse_block_scalar(int parent_indent, bool literal) {
    char indicator = literal ? '|' : '>';
    if (eof() || *current_ != indicator) return "";
    advance();  // consume | or >
    while (!eof() && *current_ != '\n') {
        char c = *current_;
        if (c == '-' || c == '+') { advance(); break; }
        if (c >= '1' && c <= '9') { advance(); break; }
        if (c == ' ' || c == '\t') advance();
        else break;
    }
    while (!eof() && *current_ != '\n') advance();
    if (!eof()) advance();
    if (eof()) return "";

    std::string result;
    int content_indent = -1;
    bool prev_was_blank = false;

    while (!eof() && current_ < end_) {
        int line_indent = get_current_indent();
        const char* line_start = current_;
        const char* line_end = simd_utils::find_char_simd(current_, end_, '\n');
        if (line_end >= end_) line_end = end_;  // no newline, use end
        bool blank = true;
        const char* p = line_start;
        while (p < line_end && (*p == ' ' || *p == '\t' || *p == '\r')) ++p;
        if (p < line_end && *p != '#' && *p != '\n') blank = false;

        if (content_indent < 0 && !blank) content_indent = line_indent;
        if (content_indent >= 0 && !blank && line_indent < content_indent) break;

        if (blank) {
            if (content_indent >= 0) result += '\n';  // blank line = newline (PyYAML compat)
            prev_was_blank = true;
        } else {
            if (content_indent >= 0) {
                const char* content_end = p;
                while (content_end < line_end && *content_end != '#') ++content_end;
                while (content_end > p && (content_end[-1] == ' ' || content_end[-1] == '\t')) --content_end;
                if (literal) {
                    if (!result.empty() && result.back() != '\n') result += '\n';
                    result.append(p, content_end);
                    result += '\n';
                } else {
                    if (!result.empty() && !prev_was_blank) result += ' ';
                    result.append(p, content_end);
                    while (!result.empty() && result.back() == ' ') result.pop_back();
                }
            }
            prev_was_blank = false;
        }
        current_ = line_end;
        if (current_ >= end_) break;
        advance();  // skip newline
    }

    while (!result.empty() && (result.back() == '\n' || result.back() == ' ')) result.pop_back();
    return result;
}

String YamlParser::parse_key_flow() {
    skip_whitespace_no_nl();
    if (eof()) return "";
    if (*current_ == '"') return parse_quoted_string('"');
    if (*current_ == '\'') return parse_quoted_string('\'');
    std::string result;
    while (!eof()) {
        char c = *current_;
        if (c == ':' || c == ',' || c == ']' || c == '}' || c == '#' || c == '\n') break;
        if (c == ' ' || c == '\t') {
            const char* next = current_;
            while (next < end_ && (*next == ' ' || *next == '\t')) ++next;
            if (next < end_ && (*next == ':' || *next == ',' || *next == ']' || *next == '}' || *next == '\n' || *next == '#')) break;
        }
        result += advance();
    }
    while (!result.empty() && (result.back() == ' ' || result.back() == '\t')) result.pop_back();
    return result;
}

YamlValue YamlParser::parse_value_flow() {
    skip_whitespace_no_nl();
    if (eof()) return Null{};

    auto alias_val = try_parse_alias();
    if (alias_val) return *alias_val;

    std::optional<std::string> anchor_name = try_parse_anchor();
    if (anchor_name) skip_whitespace_no_nl();

    YamlValue v{};
    auto b = try_parse_bool();
    if (b) { v = *b; if (anchor_name) anchors_[*anchor_name] = v; return v; }
    auto n = try_parse_null();
    if (n) { v = *n; if (anchor_name) anchors_[*anchor_name] = v; return v; }
    auto num = try_parse_number();
    if (num) { v = *num; if (anchor_name) anchors_[*anchor_name] = v; return v; }

    if (*current_ == '"' || *current_ == '\'') {
        v = YamlValue(parse_scalar());
        if (anchor_name) anchors_[*anchor_name] = v;
        return v;
    }
    if (*current_ == '[') {
        v = parse_flow_sequence();
        if (anchor_name) anchors_[*anchor_name] = v;
        return v;
    }
    if (*current_ == '{') {
        v = parse_flow_mapping();
        if (anchor_name) anchors_[*anchor_name] = v;
        return v;
    }

    v = YamlValue(parse_scalar_flow());
    if (anchor_name) anchors_[*anchor_name] = v;
    return v;
}

YamlValue YamlParser::parse_value(int indent) {
    skip_whitespace_no_nl();
    if (eof()) return Null{};

    auto alias_val = try_parse_alias();
    if (alias_val) return *alias_val;

    std::optional<std::string> anchor_name = try_parse_anchor();
    if (anchor_name) skip_whitespace_no_nl();

    // Try bool, null, number first
    YamlValue v;
    auto b = try_parse_bool();
    if (b) { v = *b; if (anchor_name) anchors_[*anchor_name] = v; return v; }
    auto n = try_parse_null();
    if (n) { v = *n; if (anchor_name) anchors_[*anchor_name] = v; return v; }
    auto num = try_parse_number();
    if (num) { v = *num; if (anchor_name) anchors_[*anchor_name] = v; return v; }

    // Quoted string
    if (*current_ == '"' || *current_ == '\'') {
        v = YamlValue(parse_scalar());
        if (anchor_name) anchors_[*anchor_name] = v;
        return v;
    }

    // Block scalar | or >
    if (*current_ == '|' || *current_ == '>') {
        bool lit = (*current_ == '|');
        v = YamlValue(parse_block_scalar(indent, lit));
        if (anchor_name) anchors_[*anchor_name] = v;
        return v;
    }
    // Flow sequence [a, b, c]
    if (*current_ == '[') {
        v = parse_flow_sequence();
        if (anchor_name) anchors_[*anchor_name] = v;
        return v;
    }
    // Flow mapping {a: 1, b: 2}
    if (*current_ == '{') {
        v = parse_flow_mapping();
        if (anchor_name) anchors_[*anchor_name] = v;
        return v;
    }

    // Check for sequence: "- value"
    if (*current_ == '-' && (current_ + 1 >= end_ || current_[1] == ' ' || current_[1] == '\t')) {
        advance();
        skip_whitespace_no_nl();
        v = parse_value(indent);
        if (anchor_name) anchors_[*anchor_name] = v;
        return v;
    }

    // Check for mapping: "key: value" - only on current line
    const char* line_end = simd_utils::find_char_simd(current_, end_, '\n');
    const char* colon = simd_utils::find_char_simd(current_, line_end, ':');
    if (colon < line_end) {
        const char* after_colon = colon + 1;
        bool key_ok = true;
        if (colon > current_) {
            const char* p = current_;
            while (p < colon) {
                if (*p == '\n' || *p == '#') {
                    key_ok = false;
                    break;
                }
                ++p;
            }
        }
        if (key_ok && (after_colon >= line_end || *after_colon == ' ' || *after_colon == '\t' || *after_colon == '\n')) {
            std::string key_str(current_, colon);
            current_ = colon + 1;
            skip_whitespace_no_nl();
            if (key_str.empty()) {
                set_error("Empty mapping key");
                return Null{};
            }
            // Trim key
            while (!key_str.empty() && (key_str.back() == ' ' || key_str.back() == '\t')) key_str.pop_back();

            YamlValue val;
            skip_whitespace_no_nl();
            if (eof() || *current_ == '\n' || *current_ == '#') {
                val = Null{};
            } else if (*current_ == '|' || *current_ == '>') {
                bool lit = (*current_ == '|');
                return YamlValue(parse_block_scalar(indent, lit));
            } else {
                val = parse_value(indent);
            }
            auto mapping = std::make_shared<Mapping>();
            if (key_str == "<<") {
                merge_into(*mapping, val);
            } else {
                mapping->set(key_str, val);
            }
            v = YamlValue(mapping);
            if (anchor_name) anchors_[*anchor_name] = v;
            return v;
        }
    }

    // Plain scalar
    v = YamlValue(parse_scalar());
    if (anchor_name) anchors_[*anchor_name] = v;
    return v;
}

YamlValue YamlParser::parse_flow_sequence() {
    expect_char('[');
    auto seq = std::make_shared<Sequence>();
    skip_whitespace_no_nl();
    if (eof()) return YamlValue(seq);
    if (*current_ == ']') {
        advance();
        return YamlValue(seq);
    }
    while (!eof()) {
        seq->append(parse_value_flow());
        skip_whitespace_no_nl();
        if (eof()) break;
        if (*current_ == ']') {
            advance();
            break;
        }
        if (*current_ == ',') {
            advance();
            skip_whitespace_no_nl();
        } else {
            break;
        }
    }
    return YamlValue(seq);
}

YamlValue YamlParser::parse_flow_mapping() {
    expect_char('{');
    auto mapping = std::make_shared<Mapping>();
    skip_whitespace_no_nl();
    if (eof()) return YamlValue(mapping);
    if (*current_ == '}') {
        advance();
        return YamlValue(mapping);
    }
    while (!eof()) {
        std::string key_str = parse_key_flow();
        skip_whitespace_no_nl();
        if (eof() || *current_ != ':') break;
        if (key_str.empty()) {
            set_error("Empty flow mapping key");
            return YamlValue(mapping);
        }
        advance();  // consume ':'
        skip_whitespace_no_nl();
        YamlValue val = eof() ? Null{} : parse_value_flow();
        if (key_str == "<<") {
            merge_into(*mapping, val);
        } else {
            mapping->set(key_str, val);
        }
        skip_whitespace_no_nl();
        if (eof()) break;
        if (*current_ == '}') {
            advance();
            break;
        }
        if (*current_ == ',') {
            advance();
            skip_whitespace_no_nl();
        } else {
            break;
        }
    }
    return YamlValue(mapping);
}

YamlValue YamlParser::parse_sequence(int base_indent) {
    auto seq = std::make_shared<Sequence>();
    bool first_item = true;
    while (!eof()) {
        int ind = get_current_indent();
        if (ind > 0 && ind < base_indent) break;  // Sibling line — stop before consuming
        // Break when we see a line at indent 0 (sibling/parent) — but not on first item,
        // since caller may have positioned us at content (e.g. mapping value)
        if (!first_item && ind == 0 && base_indent > 0) break;
        first_item = false;
        skip_blank_lines();
        if (eof()) break;
        current_ = simd_utils::skip_whitespace_no_nl(current_, end_);  // skip to content
        if (eof() || *current_ == '\n') break;
        if (*current_ != '-') break;
        advance();
        skip_whitespace_no_nl();
        if (eof() || *current_ == '\n' || *current_ == '#') {
            // "-" on its own line: might be nested sequence on next line
            skip_to_next_line();
            skip_blank_lines_only();  // don't use skip_blank_lines — it would advance past indent
            if (!eof()) {
                int next_ind = get_current_indent();
                const char* content = simd_utils::skip_whitespace_no_nl(current_, end_);
                if (next_ind > base_indent && content < end_ && *content == '-') {
                    seq->append(parse_sequence(next_ind));
                    continue;
                }
            }
            seq->append(Null{});
        } else {
            const char* line_end = simd_utils::find_char_simd(current_, end_, '\n');
            const char* colon = simd_utils::find_char_simd(current_, line_end, ':');
            bool looks_like_mapping = (colon < line_end && colon > current_ &&
                (colon[1] == ' ' || colon[1] == '\t' || colon[1] == '\n'));
            if (looks_like_mapping) {
                int mapping_base = ind + 2;
                YamlValue v = parse_mapping(mapping_base, true);  // at content, no leading indent
                seq->append(v);
                // parse_mapping leaves current_ at next line, no skip needed
            } else {
                YamlValue v = parse_value(ind);
                seq->append(v);
                // Only skip if we're still on same line (block scalar advances to next line)
                if (!eof() && *current_ == '\n') skip_to_next_line();
            }
        }
    }
    return YamlValue(seq);
}

YamlValue YamlParser::parse_mapping(int base_indent, bool at_content_start) {
    auto mapping = std::make_shared<Mapping>();
    bool first_key = true;
    while (!eof()) {
        skip_to_next_content_line();  // Position at next content line (preserve indent)
        if (eof()) break;
        int ind = get_current_indent();
        // Break when line has smaller indent (sibling/parent). Exception: first line when
        // at_content_start (caller positioned us at content, no leading spaces -> ind=0).
        if (ind < base_indent && (ind > 0 || !at_content_start || !first_key)) break;
        const char* line_start = simd_utils::skip_whitespace_no_nl(current_, end_);
        if (line_start >= end_ || *line_start == '\n') break;

        // Sequence item at same level - stop
        if (*line_start == '-' && (line_start + 1 >= end_ || line_start[1] == ' ' || line_start[1] == '\t')) {
            break;
        }
        current_ = line_start;

        const char* line_end = simd_utils::find_char_simd(current_, end_, '\n');
        const char* colon = simd_utils::find_char_simd(current_, line_end, ':');
        if (colon >= line_end) break;
        if (colon == current_) {
            set_error("Empty mapping key");
            break;
        }
        std::string key_str(current_, colon);
        current_ = colon + 1;
        skip_whitespace_no_nl();
        while (!key_str.empty() && (key_str.back() == ' ' || key_str.back() == '\t')) key_str.pop_back();
        if (key_str.empty()) break;

        YamlValue val;
        bool had_inline_value = false;
        std::optional<std::string> block_anchor;
        if (*current_ == '&') {
            auto an = try_parse_anchor();
            if (an) {
                skip_whitespace_no_nl();
                if (eof() || *current_ == '\n' || *current_ == '#') {
                    block_anchor = an;
                } else {
                    val = parse_value(ind);
                    anchors_[*an] = val;
                    had_inline_value = true;
                }
            }
        }
        if (!had_inline_value) {
        if (block_anchor || eof() || *current_ == '\n' || *current_ == '#') {
            skip_to_next_line();
            if (!eof()) {
                skip_blank_lines_only();
                if (!eof()) {
                    int next_indent = get_current_indent();
                    if (next_indent > ind) {
                        const char* content = simd_utils::skip_whitespace_no_nl(current_, end_);
                        if (content < end_ && (*content == '|' || *content == '>')) {
                            current_ = content;
                            val = YamlValue(parse_block_scalar(ind, *content == '|'));
                        } else if (content < end_ && *content == '-') {
                            current_ = content;
                            val = parse_sequence(next_indent);
                        } else {
                            val = parse_mapping(next_indent, false);
                        }
                        if (block_anchor) anchors_[*block_anchor] = val;
                    } else {
                        val = Null{};
                    }
                } else {
                    val = Null{};
                }
            } else {
                val = Null{};
            }
        } else {
            val = parse_value(ind);
            had_inline_value = true;
        }
        }

        if (key_str == "<<") {
            merge_into(*mapping, val);
        } else {
            mapping->set(key_str, val);
        }
        first_key = false;

        if (eof()) break;
        if (had_inline_value) {
            skip_to_next_line();
        }
    }
    return YamlValue(mapping);
}

void YamlParser::skip_document_prefix() {
    skip_blank_lines();
    while (!eof()) {
        int ind = get_current_indent();
        if (ind > 0) break;  // Indented line - not directive or marker
        const char* line_start = simd_utils::skip_whitespace_no_nl(current_, end_);
        if (line_start >= end_ || *line_start == '\n') break;
        if (*line_start == '%') {
            current_ = line_start;
            skip_to_next_line();
            skip_blank_lines();
            continue;
        }
        if (line_start + 3 <= end_ && line_start[0] == '-' && line_start[1] == '-' &&
            line_start[2] == '-') {
            current_ = line_start + 3;
            skip_whitespace_no_nl();
            if (!eof() && (*current_ == '|' || *current_ == '>')) {
                break;  // --- | or --- > : document is block scalar, leave | or > for parsing
            }
            skip_to_next_line();
            skip_blank_lines();
            continue;
        }
        break;
    }
}

YamlValue YamlParser::parse_document() {
    skip_document_prefix();
    if (eof()) {
        return YamlValue(std::make_shared<Mapping>());
    }

    int base_indent = get_current_indent();

    // Block scalar at root (e.g. --- | or --- >)
    if (*current_ == '|' || *current_ == '>') {
        bool lit = (*current_ == '|');
        return YamlValue(parse_block_scalar(0, lit));
    }
    // Flow at root
    if (*current_ == '[') return parse_flow_sequence();
    if (*current_ == '{') return parse_flow_mapping();

    // Sequence at root ("- item" or "-" on own line with nested content)
    if (*current_ == '-' && (current_ + 1 >= end_ || current_[1] == ' ' || current_[1] == '\t' || current_[1] == '\n')) {
        return parse_sequence(base_indent);
    }

    // Root-level scalar: null, bool, number, quoted string (document is a single value)
    auto n = try_parse_null();
    if (n) return *n;
    auto b = try_parse_bool();
    if (b) return *b;
    auto num = try_parse_number();
    if (num) return *num;
    if (*current_ == '"' || *current_ == '\'') {
        return YamlValue(parse_scalar());
    }
    // Plain scalar at root: no colon on line (colon indicates mapping key: value)
    const char* line_end = simd_utils::find_char_simd(current_, end_, '\n');
    const char* colon = simd_utils::find_char_simd(current_, line_end, ':');
    if (colon >= line_end) {
        return YamlValue(parse_unquoted_scalar());
    }

    // Mapping at root
    return parse_mapping(base_indent);
}

void YamlParser::skip_document_suffix() {
    skip_whitespace();
    if (current_ + 3 <= end_ && current_[0] == '.' && current_[1] == '.' && current_[2] == '.' &&
        (current_ + 3 >= end_ || current_[3] == ' ' || current_[3] == '\t' || current_[3] == '\n' || current_[3] == '#')) {
        current_ += 3;
        skip_to_next_line();
    }
    skip_whitespace();
    skip_comment();
    skip_whitespace();
}

YamlValue YamlParser::parse(const std::string& input) {
    error_message_.clear();
    current_ = input.data();
    end_ = input.data() + input.size();
    indent_stack_.clear();
    anchors_.clear();

    YamlValue result = parse_document();
    skip_document_suffix();
    return result;
}

std::vector<YamlValue> YamlParser::parse_all(const std::string& input) {
    error_message_.clear();
    current_ = input.data();
    end_ = input.data() + input.size();
    indent_stack_.clear();
    anchors_.clear();

    std::vector<YamlValue> docs;
    skip_document_prefix();
    if (eof()) return docs;

    while (!eof()) {
        docs.push_back(parse_document());
        skip_document_suffix();
    }
    return docs;
}

}  // namespace fastyaml

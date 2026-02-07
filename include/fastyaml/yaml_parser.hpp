#pragma once

#include <string>
#include <variant>
#include <vector>
#include <unordered_map>
#include <memory>
#include <optional>
#include <cstdint>
#include <vector>

namespace fastyaml {

// Forward declarations
class Value;
class Mapping;
class Sequence;

// YAML value types (MVP subset)
using Integer = int64_t;
using Float = double;
using Boolean = bool;
using String = std::string;
using MappingPtr = std::shared_ptr<Mapping>;
using SequencePtr = std::shared_ptr<Sequence>;

// Null type marker
struct Null {};

// YAML value variant
using YamlValue = std::variant<
    Null,
    Integer,
    Float,
    Boolean,
    String,
    MappingPtr,
    SequencePtr
>;

// YAML Mapping (key-value pairs, like dict)
class Mapping {
public:
    std::unordered_map<std::string, YamlValue> values;

    void set(const std::string& key, const YamlValue& value) {
        values[key] = value;
    }

    bool has(const std::string& key) const {
        return values.find(key) != values.end();
    }
};

// YAML Sequence (list of values)
class Sequence {
public:
    std::vector<YamlValue> elements;

    void append(const YamlValue& value) {
        elements.push_back(value);
    }

    size_t size() const {
        return elements.size();
    }
};

// SIMD-optimized utility functions
namespace simd_utils {
    const char* skip_whitespace(const char* ptr, const char* end);
    const char* skip_whitespace_no_nl(const char* ptr, const char* end);
    const char* find_char_simd(const char* ptr, const char* end, char c);
    const char* find_char_in_line(const char* ptr, const char* end, char c);
    bool is_whitespace(char c);
}

// YAML Parser (MVP: basic subset for configs)
class YamlParser {
public:
    YamlParser();
    ~YamlParser();

    // Parse YAML string, returns root value (Mapping or Sequence)
    YamlValue parse(const std::string& input);

    // Parse all documents in stream (multi-document), returns vector of documents
    std::vector<YamlValue> parse_all(const std::string& input);

    // Get parse error if any
    std::string get_error() const { return error_message_; }
    bool has_error() const { return !error_message_.empty(); }

private:
    std::string error_message_;
    const char* current_;
    const char* end_;
    std::vector<int> indent_stack_;  // Track indentation levels (2 spaces)
    std::unordered_map<std::string, YamlValue> anchors_;  // &name -> value for *alias

    // Parse methods
    YamlValue parse_document();
    YamlValue parse_value(int indent);
    YamlValue parse_value_flow();  // For use inside flow, scalars stop at , ] } [
    YamlValue parse_mapping(int base_indent, bool at_content_start = false);
    YamlValue parse_sequence(int base_indent);
    YamlValue parse_flow_sequence();
    YamlValue parse_flow_mapping();
    String parse_scalar();
    String parse_scalar_flow();  // Unquoted scalar stopping at flow delimiters , ] } [
    String parse_key_flow();     // Key in flow mapping, stops at :
    String parse_quoted_string(char quote);
    String parse_unquoted_scalar();
    String parse_block_scalar(int parent_indent, bool literal);  // | literal, > folded
    std::optional<std::string> try_parse_anchor();   // &name, returns name
    std::optional<YamlValue> try_parse_alias();      // *name, returns anchored value
    std::optional<YamlValue> try_parse_bool();
    std::optional<YamlValue> try_parse_null();
    std::optional<YamlValue> try_parse_number();
    Integer parse_integer(const std::string& str);
    Float parse_float(const std::string& str);

    void merge_into(Mapping& target, const YamlValue& val);  // Merge key <<
    void skip_document_prefix();   // Skip %directives and ---
    void skip_document_suffix();   // Skip optional ...
    // Line/indent helpers
    int get_current_indent();
    void skip_to_next_line();
    void skip_blank_lines();
    void skip_blank_lines_only();  // Skip whole blank/comment lines, preserve indent of first content line
    void skip_to_next_content_line();  // Skip newlines/blank/comment lines, leave at content line start (with indent)
    bool at_line_start();

    // Utility methods
    void skip_whitespace();
    void skip_whitespace_no_nl();
    void skip_comment();
    void expect_char(char c);
    bool peek_char(char c);
    char peek();
    char advance();
    bool eof();
    void set_error(const std::string& message);

    std::string parse_escape_sequence();
};

}  // namespace fastyaml

import Foundation

// MARK: - Shared models (mirror the FastAPI backend shapes)

struct SupportResource: Codable {
    let name: String
    let contact: String
}

struct SupportPayload: Codable {
    let crisisFlag: Bool
    let message: String
    let resources: [SupportResource]
}

// POST /home/recommend
struct Recommendation: Codable {
    let feature: String          // "journal" | "sleep" | "coping" | "none"
    let title: String
    let reason: String
    let exerciseId: String?
}

struct RecommendResponse: Codable {
    let reply: String
    let recommendation: Recommendation
    let crisisFlag: Bool
    let support: SupportPayload?
}

// Coping library
struct ExerciseSummary: Codable, Identifiable {
    let id: String
    let title: String
    let category: String
    let durationMinutes: Int
}

struct ExerciseStep: Codable {
    let title: String
    let instruction: String
}

struct ExerciseDetail: Codable, Identifiable {
    let id: String
    let title: String
    let category: String
    let durationMinutes: Int
    let maritimeNote: String
    let steps: [ExerciseStep]
}

// Coping sessions
struct SessionDeferred: Codable {
    let status: String
    let message: String
}

struct CopingSessionOut: Codable, Identifiable {
    let id: Int
    let createdAt: String
    let exerciseId: String
    let exerciseTitle: String
    let moodBefore: Int
    let moodAfter: Int?
    let moodShift: Int?
    let completed: Bool
    let crisisFlag: Bool
    let support: SupportPayload?
    let exercise: ExerciseDetail?
}

// Journal
struct JournalEntry: Codable, Identifiable {
    let id: Int
    let createdAt: String
    let title: String?
    let body: String
    let moodBefore: Int?
    let moodAfter: Int?
    let tags: String?
    let crisisFlag: Bool
    let support: SupportPayload?
}

// Mood
struct MoodCheckinOut: Codable {
    let id: Int
    let createdAt: String
    let score: Int
    let note: String?
}

// Sleep
struct WatchSchedule: Codable {
    let id: Int
    let name: String
    let watch1Start: String
    let watch1End: String
    let watch2Start: String?
    let watch2End: String?
}

struct SleepLog: Codable, Identifiable {
    let id: Int
    let sleepDate: String
    let bedtime: String
    let wakeTime: String
    let durationHours: Double
    let quality: Int?
    let noiseLevel: Int?
    let interruptions: Int
    let notes: String?
    let watchOverlapWarning: Bool
    let crisisFlag: Bool
    let support: SupportPayload?
}

struct SleepWindow: Codable {
    let start: String
    let end: String
    let hours: Double
}

struct NapGap: Codable {
    let start: String
    let end: String
    let hours: Double
}

struct SleepPlan: Codable {
    let sleepWindow: SleepWindow?
    let strategy: String?
    let secondaryNapGaps: [NapGap]?
    let caffeineCutoff: String?
    let lightGuidance: String?
    let windDownRoutine: [String]?
    let noiseTip: String?
    let noSleepZones: [String]?
    let safetyNotice: String?
    let watchSchedule: String?
    let note: String?
}

struct SleepDebt: Codable {
    let daysLogged: Int
    let avgSleepHours: Double
    let avgQuality: Double?
    let sleepDebtHoursPerNight: Double
    let fatigueBand: String
    let disclaimer: String
}

// MARK: - API errors

enum APIError: LocalizedError {
    case http(status: Int, detail: String)
    case decoding
    case network(Error)

    var errorDescription: String? {
        switch self {
        case .http(_, let detail): return detail
        case .decoding: return "Couldn't understand the server's reply."
        case .network(let e): return e.localizedDescription
        }
    }
}

// MARK: - Client

final class APIClient {
    static let shared = APIClient()

    // Your Mac mini's Tailscale IP. Change this if it ever changes.
    // Tailscale must be connected on this iPhone for the app to reach the server.
    static let baseURL = "http://100.113.54.16:8000"

    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }()

    private let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.keyEncodingStrategy = .convertToSnakeCase
        return e
    }()

    private func url(_ path: String) -> URL {
        URL(string: Self.baseURL + path)!
    }

    private func decodeError(_ data: Data, status: Int) -> APIError {
        if let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let detail = obj["detail"] as? String {
            return .http(status: status, detail: detail)
        }
        return .http(status: status, detail: "Request failed (status \(status)).")
    }

    private func get<T: Decodable>(_ path: String) async throws -> T {
        do {
            let (data, response) = try await URLSession.shared.data(from: url(path))
            guard let http = response as? HTTPURLResponse else { throw APIError.decoding }
            guard (200..<300).contains(http.statusCode) else { throw decodeError(data, status: http.statusCode) }
            guard let value = try? decoder.decode(T.self, from: data) else { throw APIError.decoding }
            return value
        } catch let e as APIError {
            throw e
        } catch {
            throw APIError.network(error)
        }
    }

    private func post<Body: Encodable, T: Decodable>(_ path: String, body: Body, expected: [Int] = [200, 201]) async throws -> (T, Int) {
        var req = URLRequest(url: url(path))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try encoder.encode(body)
        do {
            let (data, response) = try await URLSession.shared.data(for: req)
            guard let http = response as? HTTPURLResponse else { throw APIError.decoding }
            guard expected.contains(http.statusCode) else { throw decodeError(data, status: http.statusCode) }
            guard let value = try? decoder.decode(T.self, from: data) else { throw APIError.decoding }
            return (value, http.statusCode)
        } catch let e as APIError {
            throw e
        } catch {
            throw APIError.network(error)
        }
    }

    // MARK: Home

    struct RecommendBody: Encodable {
        let message: String?
        let mood: Int?
        let name: String?
    }

    func recommend(message: String?, mood: Int?, name: String?) async throws -> RecommendResponse {
        let (value, _): (RecommendResponse, Int) = try await post(
            "/home/recommend",
            body: RecommendBody(message: message, mood: mood, name: name)
        )
        return value
    }

    // MARK: Coping

    struct ExerciseList: Decodable {
        let exercises: [ExerciseSummary]
    }

    func listExercises() async throws -> [ExerciseSummary] {
        let list: ExerciseList = try await get("/coping/exercises")
        return list.exercises
    }

    func exerciseDetail(id: String) async throws -> ExerciseDetail {
        let detail: ExerciseDetail = try await get("/coping/exercises/\(id)")
        return detail
    }

    struct SessionStartBody: Encodable {
        let exerciseId: String
        let moodBefore: Int
        let onWatch: Bool
        let note: String?
    }

    enum SessionStartResult {
        case started(CopingSessionOut)
        case deferred(String)
    }

    /// Starts a session. Returns `.deferred` when on watch (HTTP 200),
    /// `.started` on 201. Throws APIError on 404/429.
    func startSession(exerciseId: String, mood: Int, onWatch: Bool, note: String?) async throws -> SessionStartResult {
        var req = URLRequest(url: url("/coping/sessions/start"))
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try encoder.encode(SessionStartBody(exerciseId: exerciseId, moodBefore: mood, onWatch: onWatch, note: note))
        let (data, response) = try await URLSession.shared.data(for: req)
        guard let http = response as? HTTPURLResponse else { throw APIError.decoding }
        switch http.statusCode {
        case 200:
            guard let d = try? decoder.decode(SessionDeferred.self, from: data) else { throw APIError.decoding }
            return .deferred(d.message)
        case 201:
            guard let s = try? decoder.decode(CopingSessionOut.self, from: data) else { throw APIError.decoding }
            return .started(s)
        default:
            throw decodeError(data, status: http.statusCode)
        }
    }

    struct SessionCompleteBody: Encodable {
        let moodAfter: Int
    }

    func completeSession(id: Int, moodAfter: Int) async throws -> CopingSessionOut {
        let (value, _): (CopingSessionOut, Int) = try await post(
            "/coping/sessions/\(id)/complete",
            body: SessionCompleteBody(moodAfter: moodAfter)
        )
        return value
    }

    // MARK: Journal

    struct JournalCreateBody: Encodable {
        let title: String?
        let body: String
        let moodBefore: Int?
    }

    func listJournal() async throws -> [JournalEntry] {
        let entries: [JournalEntry] = try await get("/journal/entries")
        return entries
    }

    func createJournal(body: String, moodBefore: Int?) async throws -> JournalEntry {
        let (value, _): (JournalEntry, Int) = try await post(
            "/journal/entries",
            body: JournalCreateBody(title: nil, body: body, moodBefore: moodBefore)
        )
        return value
    }

    // MARK: Mood

    struct MoodBody: Encodable {
        let score: Int
        let note: String?
    }

    func moodCheckin(score: Int) async throws -> MoodCheckinOut {
        let (value, _): (MoodCheckinOut, Int) = try await post(
            "/mood/checkin",
            body: MoodBody(score: score, note: nil)
        )
        return value
    }

    // MARK: Sleep

    struct WatchScheduleBody: Encodable {
        let name: String
        let watch1Start: String
        let watch1End: String
        let watch2Start: String?
        let watch2End: String?
    }

    func getWatchSchedule() async throws -> WatchSchedule? {
        do {
            return try await get("/sleep/watch-schedule")
        } catch APIError.http(let status, _) where status == 404 {
            return nil
        }
    }

    func setWatchSchedule(name: String, w1Start: String, w1End: String, w2Start: String?, w2End: String?) async throws -> WatchSchedule {
        let (value, _): (WatchSchedule, Int) = try await post(
            "/sleep/watch-schedule",
            body: WatchScheduleBody(name: name, watch1Start: w1Start, watch1End: w1End, watch2Start: w2Start, watch2End: w2End)
        )
        return value
    }

    struct SleepLogBody: Encodable {
        let sleepDate: String
        let bedtime: String
        let wakeTime: String
        let quality: Int?
    }

    func listSleepLogs() async throws -> [SleepLog] {
        let logs: [SleepLog] = try await get("/sleep/logs")
        return logs
    }

    func logSleep(date: String, bedtime: String, wakeTime: String, quality: Int?) async throws -> SleepLog {
        let (value, _): (SleepLog, Int) = try await post(
            "/sleep/logs",
            body: SleepLogBody(sleepDate: date, bedtime: bedtime, wakeTime: wakeTime, quality: quality)
        )
        return value
    }

    func sleepPlan() async throws -> SleepPlan {
        try await get("/sleep/plan")
    }

    func sleepDebt() async throws -> SleepDebt {
        try await get("/sleep/debt")
    }
}

// MARK: - Helpers

extension APIClient {
    /// ISO8601 "2026-10-04T03:12:00" → "Oct 4, 3:12 AM"
    static func displayDate(_ iso: String) -> String {
        let parser = ISO8601DateFormatter()
        parser.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = parser.date(from: iso) { return short(date) }
        parser.formatOptions = [.withInternetDateTime]
        if let date = parser.date(from: iso) { return short(date) }
        return iso
    }

    private static func short(_ date: Date) -> String {
        let f = DateFormatter()
        f.dateStyle = .medium
        f.timeStyle = .short
        return f.string(from: date)
    }
}

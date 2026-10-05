import SwiftUI

struct SleepView: View {
    @State private var schedule: WatchSchedule? = nil
    @State private var plan: SleepPlan? = nil
    @State private var debt: SleepDebt? = nil
    @State private var logs: [SleepLog] = []
    @State private var isLoading = true
    @State private var errorText: String? = nil

    // Schedule setup form
    @State private var w1Start = "04:00"
    @State private var w1End = "08:00"
    @State private var w2Start = "16:00"
    @State private var w2End = "20:00"
    @State private var useSecondWatch = true
    @State private var isSavingSchedule = false

    // Log form
    @State private var bedtime = "22:30"
    @State private var wakeTime = "06:00"
    @State private var quality: Int? = nil
    @State private var isLogging = false

    var body: some View {
        ZStack {
            CalmBackground()
            Group {
                if isLoading {
                    ProgressView().tint(.white)
                } else if schedule == nil {
                    scheduleSetup
                } else {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 20) {
                            planCard
                            debtCard
                            logForm
                            logList
                            DisclaimerFooter()
                        }
                        .padding()
                    }
                }
            }
        }
        .navigationTitle("Sleep")
        .task { await load() }
        .alert("Something went wrong", isPresented: .constant(errorText != nil)) {
            Button("OK") { errorText = nil }
        } message: {
            Text(errorText ?? "")
        }
    }

    // MARK: - Schedule setup

    private var scheduleSetup: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("When are your watches?")
                    .font(.largeTitle)
                    .fontWeight(.semibold)
                    .foregroundStyle(.white.opacity(0.95))
                Text("Ocyni only ever plans sleep in your off-duty hours. Watch periods are always marked as no-sleep zones.")
                    .font(.body)
                    .foregroundStyle(.white.opacity(0.7))
                    .lineSpacing(3)

                HStack(spacing: 12) {
                    presetButton("4 / 8") {
                        w1Start = "04:00"; w1End = "08:00"
                        w2Start = "16:00"; w2End = "20:00"; useSecondWatch = true
                    }
                    presetButton("6 / 6") {
                        w1Start = "00:00"; w1End = "06:00"
                        w2Start = "12:00"; w2End = "18:00"; useSecondWatch = true
                    }
                }

                SoftCard {
                    VStack(spacing: 14) {
                        watchField("Watch 1 start", $w1Start)
                        watchField("Watch 1 end", $w1End)
                        Toggle("Two watches per day", isOn: $useSecondWatch)
                            .foregroundStyle(.white.opacity(0.85))
                        if useSecondWatch {
                            watchField("Watch 2 start", $w2Start)
                            watchField("Watch 2 end", $w2End)
                        }
                        Button {
                            saveSchedule()
                        } label: {
                            HStack {
                                if isSavingSchedule { ProgressView().tint(.white) }
                                Text("Save watch schedule")
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.teal.opacity(0.65))
                        .disabled(isSavingSchedule)
                    }
                }
                DisclaimerFooter()
            }
            .padding()
        }
    }

    private func presetButton(_ title: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
        }
        .buttonStyle(.bordered)
        .tint(.teal)
    }

    private func watchField(_ label: String, _ value: Binding<String>) -> some View {
        HStack {
            Text(label).foregroundStyle(.white.opacity(0.8))
            Spacer()
            TextField("HH:MM", text: value)
                .keyboardType(.numbersAndPunctuation)
                .multilineTextAlignment(.trailing)
                .frame(width: 90)
                .padding(8)
                .background(.white.opacity(0.08))
                .clipShape(RoundedRectangle(cornerRadius: 10))
                .foregroundStyle(.white)
        }
    }

    private func saveSchedule() {
        isSavingSchedule = true
        Task {
            do {
                let name = useSecondWatch ? "custom" : "single"
                let s = try await APIClient.shared.setWatchSchedule(
                    name: name,
                    w1Start: w1Start, w1End: w1End,
                    w2Start: useSecondWatch ? w2Start : nil,
                    w2End: useSecondWatch ? w2End : nil
                )
                await MainActor.run {
                    schedule = s
                    isSavingSchedule = false
                }
                await load()
            } catch {
                await MainActor.run {
                    errorText = error.localizedDescription
                    isSavingSchedule = false
                }
            }
        }
    }

    // MARK: - Plan card

    @ViewBuilder
    private var planCard: some View {
        if let plan {
            SoftCard {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Your sleep plan")
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundStyle(.white.opacity(0.95))
                    if let window = plan.sleepWindow {
                        Text("Sleep \(window.start) – \(window.end) (\(String(format: "%.1f", window.hours)) h)")
                            .font(.headline)
                            .foregroundStyle(.teal.opacity(0.95))
                    }
                    if let strategy = plan.strategy {
                        Text(strategy).font(.body).foregroundStyle(.white.opacity(0.85)).lineSpacing(3)
                    }
                    if let gaps = plan.secondaryNapGaps, !gaps.isEmpty {
                        Text("Nap gaps")
                            .font(.subheadline).foregroundStyle(.white.opacity(0.7))
                        ForEach(gaps, id: \.start) { g in
                            Text("· \(g.start) – \(g.end) (\(String(format: "%.1f", g.hours)) h)")
                                .font(.subheadline).foregroundStyle(.white.opacity(0.75))
                        }
                    }
                    if let c = plan.caffeineCutoff {
                        planRow(c)
                    }
                    if let l = plan.lightGuidance {
                        planRow(l)
                    }
                    if let routine = plan.windDownRoutine, !routine.isEmpty {
                        Text("Wind-down").font(.subheadline).foregroundStyle(.white.opacity(0.7))
                        ForEach(routine, id: \.self) { step in
                            Text("· \(step)").font(.subheadline).foregroundStyle(.white.opacity(0.75)).lineSpacing(2)
                        }
                    }
                    if let tip = plan.noiseTip {
                        planRow(tip)
                    }
                    if let zones = plan.noSleepZones, !zones.isEmpty {
                        Text("No-sleep zones").font(.subheadline).foregroundStyle(.red.opacity(0.85))
                        ForEach(zones, id: \.self) { z in
                            Text("· \(z)").font(.subheadline).foregroundStyle(.white.opacity(0.75))
                        }
                    }
                    if let notice = plan.safetyNotice {
                        Text(notice).font(.caption).foregroundStyle(.white.opacity(0.55))
                    }
                }
            }
        }
    }

    private func planRow(_ text: String) -> some View {
        Text(text).font(.body).foregroundStyle(.white.opacity(0.85)).lineSpacing(3)
    }

    // MARK: - Debt card

    @ViewBuilder
    private var debtCard: some View {
        if let debt {
            SoftCard {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Last 7 days")
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundStyle(.white.opacity(0.95))
                    HStack {
                        VStack(alignment: .leading) {
                            Text("\(String(format: "%.1f", debt.avgSleepHours)) h")
                                .font(.title).foregroundStyle(.white)
                            Text("avg / night").font(.caption).foregroundStyle(.white.opacity(0.6))
                        }
                        Spacer()
                        VStack(alignment: .trailing) {
                            Text(debt.fatigueBand.capitalized)
                                .font(.title3)
                                .foregroundStyle(fatigueColor(debt.fatigueBand))
                            Text("fatigue").font(.caption).foregroundStyle(.white.opacity(0.6))
                        }
                    }
                    if debt.daysLogged < 7 {
                        Text("Logged \(debt.daysLogged) of 7 nights — the more you log, the truer this gets.")
                            .font(.caption).foregroundStyle(.white.opacity(0.6))
                    }
                    Text(debt.disclaimer).font(.caption2).foregroundStyle(.white.opacity(0.45))
                }
            }
        }
    }

    private func fatigueColor(_ band: String) -> Color {
        switch band {
        case "high": return .red.opacity(0.9)
        case "moderate": return .orange.opacity(0.9)
        default: return .green.opacity(0.9)
        }
    }

    // MARK: - Log form + list

    private var logForm: some View {
        SoftCard {
            VStack(alignment: .leading, spacing: 12) {
                Text("Log last night's sleep")
                    .font(.headline)
                    .foregroundStyle(.white)
                HStack {
                    watchField("Bedtime", $bedtime)
                }
                watchField("Wake time", $wakeTime)
                Text("Quality (optional)").font(.subheadline).foregroundStyle(.white.opacity(0.7))
                MoodDots(mood: $quality)
                Button {
                    log()
                } label: {
                    HStack {
                        if isLogging { ProgressView().tint(.white) }
                        Text("Save sleep log")
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                }
                .buttonStyle(.borderedProminent)
                .tint(.teal.opacity(0.65))
                .disabled(isLogging)
            }
        }
    }

    private func log() {
        isLogging = true
        Task {
            do {
                let f = DateFormatter()
                f.dateFormat = "yyyy-MM-dd"
                let entry = try await APIClient.shared.logSleep(
                    date: f.string(from: Date()),
                    bedtime: bedtime, wakeTime: wakeTime, quality: quality
                )
                await MainActor.run {
                    logs.insert(entry, at: 0)
                    quality = nil
                    isLogging = false
                }
                await refreshDebt()
            } catch {
                await MainActor.run {
                    errorText = error.localizedDescription
                    isLogging = false
                }
            }
        }
    }

    private var logList: some View {
        VStack(alignment: .leading, spacing: 10) {
            if !logs.isEmpty {
                Text("Recent nights")
                    .font(.headline)
                    .foregroundStyle(.white.opacity(0.9))
                    .padding(.horizontal, 4)
                ForEach(logs.prefix(7)) { entry in
                    SoftCard {
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Text(entry.sleepDate)
                                    .font(.subheadline)
                                    .foregroundStyle(.white.opacity(0.8))
                                Spacer()
                                Text("\(String(format: "%.1f", entry.durationHours)) h")
                                    .font(.headline)
                                    .foregroundStyle(.white)
                            }
                            Text("\(entry.bedtime) → \(entry.wakeTime)")
                                .font(.subheadline)
                                .foregroundStyle(.white.opacity(0.6))
                            if entry.watchOverlapWarning {
                                Text("⚠ overlapped a watch — double-check the times")
                                    .font(.caption)
                                    .foregroundStyle(.orange.opacity(0.9))
                            }
                            if entry.crisisFlag, let support = entry.support {
                                CrisisSupportCard(support: support)
                            }
                        }
                    }
                }
            }
        }
    }

    // MARK: - Load

    private func load() async {
        do {
            async let sched = APIClient.shared.getWatchSchedule()
            async let lg = APIClient.shared.listSleepLogs()
            let (s, l) = try await (sched, lg)
            await MainActor.run {
                schedule = s
                logs = l
                isLoading = false
            }
            if s != nil {
                async let p = APIClient.shared.sleepPlan()
                async let d = APIClient.shared.sleepDebt()
                let (pp, dd) = try await (p, d)
                await MainActor.run {
                    plan = pp
                    debt = dd
                }
            }
        } catch {
            await MainActor.run {
                errorText = error.localizedDescription
                isLoading = false
            }
        }
    }

    private func refreshDebt() async {
        do {
            let d = try await APIClient.shared.sleepDebt()
            await MainActor.run { debt = d }
        } catch { /* quiet — the log already saved */ }
    }
}

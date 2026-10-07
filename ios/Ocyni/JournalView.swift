import SwiftUI

struct JournalView: View {
    @State private var entries: [JournalEntry] = []
    @State private var isLoading = true
    @State private var errorText: String? = nil
    @State private var showingComposer = false

    var body: some View {
        ZStack {
            CalmBackground()
            Group {
                if isLoading {
                    ProgressView().tint(.white)
                } else if entries.isEmpty {
                    VStack(spacing: 12) {
                        Text("Nothing here yet.")
                            .font(.title3)
                            .foregroundStyle(.white.opacity(0.85))
                        Text("Writing things down untangles them.\nYour journal is private — only you see it.")
                            .font(.body)
                            .foregroundStyle(.white.opacity(0.6))
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                } else {
                    List {
                        ForEach(entries) { entry in
                            VStack(alignment: .leading, spacing: 8) {
                                if let title = entry.title, !title.isEmpty {
                                    Text(title).font(.headline).foregroundStyle(.white)
                                }
                                Text(entry.body)
                                    .font(.body)
                                    .foregroundStyle(.white.opacity(0.9))
                                    .lineLimit(6)
                                HStack {
                                    Text(APIClient.displayDate(entry.createdAt))
                                        .font(.caption)
                                        .foregroundStyle(.white.opacity(0.5))
                                    if let m = entry.moodBefore {
                                        Text("Mood \(m)/5")
                                            .font(.caption)
                                            .foregroundStyle(.white.opacity(0.5))
                                    }
                                }
                                if entry.crisisFlag, let support = entry.support {
                                    CrisisSupportCard(support: support)
                                }
                            }
                            .padding(.vertical, 6)
                            .listRowBackground(Color.clear)
                            .listRowSeparator(.hidden)
                        }
                    }
                    .listStyle(.plain)
                    .scrollContentBackground(.hidden)
                }
            }
        }
        .navigationTitle("Journal")
        .toolbar {
            Button { showingComposer = true } label: {
                Image(systemName: "square.and.pencil")
            }
        }
        .sheet(isPresented: $showingComposer) {
            JournalComposer { saved in
                if let saved { entries.insert(saved, at: 0) }
                showingComposer = false
            }
        }
        .task { await load() }
        .alert("Couldn't load", isPresented: .constant(errorText != nil)) {
            Button("OK") { errorText = nil }
        } message: {
            Text(errorText ?? "")
        }
    }

    private func load() async {
        do {
            let list = try await APIClient.shared.listJournal()
            await MainActor.run {
                entries = list
                isLoading = false
            }
        } catch {
            await MainActor.run {
                errorText = error.localizedDescription
                isLoading = false
            }
        }
    }
}

private struct JournalComposer: View {
    @State private var entryBody: String = ""
    @State private var mood: Int? = nil
    @State private var isSaving = false
    @State private var errorText: String? = nil
    let onDone: (JournalEntry?) -> Void

    var body: some View {
        NavigationStack {
            ZStack {
                CalmBackground()
                VStack(alignment: .leading, spacing: 20) {
                    Text("Get it out of your head\nand onto the page.")
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundStyle(.white.opacity(0.95))
                    TextField("Write freely…", text: $entryBody, axis: .vertical)
                        .lineLimit(6...12)
                        .padding(14)
                        .background(.white.opacity(0.08))
                        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                        .foregroundStyle(.white)
                    Text("How do you feel right now?")
                        .font(.subheadline)
                        .foregroundStyle(.white.opacity(0.7))
                    MoodDots(mood: $mood)
                    if let errorText {
                        Text(errorText).font(.subheadline).foregroundStyle(.orange)
                    }
                    Spacer()
                    Button {
                        save()
                    } label: {
                        HStack {
                            if isSaving { ProgressView().tint(.white) }
                            Text("Save entry")
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.teal.opacity(0.65))
                    .disabled(entryBody.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSaving)
                    DisclaimerFooter()
                }
                .padding()
            }
            .navigationTitle("New entry")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { onDone(nil) }
                }
            }
        }
    }

    private func save() {
        isSaving = true
        Task {
            do {
                let entry = try await APIClient.shared.createJournal(
                    body: entryBody.trimmingCharacters(in: .whitespacesAndNewlines),
                    moodBefore: mood
                )
                await MainActor.run { onDone(entry) }
            } catch {
                await MainActor.run {
                    errorText = error.localizedDescription
                    isSaving = false
                }
            }
        }
    }
}
